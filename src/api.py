import os
import uuid
import tempfile
import logging

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.config import settings
from src.database import get_db
from src.models import Document, DocumentChunk
from src.services.pdf_parser import extract_text_from_pdf
from src.services.chunker import chunk_text
from src.services.embedder import generate_embeddings, embed_query

logger = logging.getLogger(__name__)

api_router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    limit: int = 5


class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    page_count: int
    chunk_count: int
    error_message: str | None
    created_at: str


# ── Document Processing (synchronous, no Celery) ─────────────────────────────

def _process_document(document_id: str) -> None:
    """Process a document: parse PDF → chunk text → embed → store vectors."""
    from src.database import SessionLocal

    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == uuid.UUID(document_id)).first()
        if not doc:
            logger.error(f"Document {document_id} not found")
            return

        doc.status = "processing"
        db.commit()

        # 1. Read PDF from temp upload path
        upload_path = os.path.join(settings.UPLOAD_DIR, f"{document_id}.pdf")
        if not os.path.exists(upload_path):
            doc.status = "failed"
            doc.error_message = "Upload file not found on disk."
            db.commit()
            return

        # 2. Extract text
        raw_text = extract_text_from_pdf(upload_path)
        if not raw_text.strip():
            doc.status = "failed"
            doc.error_message = "No text could be extracted from the PDF."
            db.commit()
            return

        # 3. Chunk
        chunks = chunk_text(raw_text)
        if not chunks:
            doc.status = "failed"
            doc.error_message = "Chunking produced no segments."
            db.commit()
            return

        # 4. Embed
        embeddings = generate_embeddings(chunks)

        # 5. Store chunks + embeddings
        for idx, (chunk_text_content, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_obj = DocumentChunk(
                document_id=doc.id,
                chunk_index=idx,
                text_content=chunk_text_content,
                embedding=embedding,
            )
            db.add(chunk_obj)

        doc.chunk_count = len(chunks)
        doc.status = "ready"
        db.commit()

        # Clean up the uploaded file
        try:
            os.remove(upload_path)
        except OSError:
            pass

        logger.info(
            f"Document {document_id} processed: {len(chunks)} chunks embedded."
        )

    except Exception as e:
        logger.exception(f"Failed to process document {document_id}")
        try:
            doc = (
                db.query(Document)
                .filter(Document.id == uuid.UUID(document_id))
                .first()
            )
            if doc:
                doc.status = "failed"
                doc.error_message = str(e)[:500]
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


# ── Endpoints ─────────────────────────────────────────────────────────────────


@api_router.post("/documents", status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a PDF document for semantic indexing."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Create DB record
    new_doc = Document(filename=file.filename, status="uploaded")
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # Save uploaded file to disk
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    upload_path = os.path.join(settings.UPLOAD_DIR, f"{new_doc.id}.pdf")
    content = await file.read()
    with open(upload_path, "wb") as f:
        f.write(content)

    # Kick off background processing (no Celery – uses FastAPI BackgroundTasks)
    background_tasks.add_task(_process_document, str(new_doc.id))

    return {
        "message": "Document uploaded successfully. Processing started.",
        "document_id": str(new_doc.id),
    }


@api_router.get("/documents")
async def list_documents(db: Session = Depends(get_db)):
    """List all documents with their processing status."""
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        {
            "id": str(d.id),
            "filename": d.filename,
            "status": d.status,
            "page_count": d.page_count or 0,
            "chunk_count": d.chunk_count or 0,
            "error_message": d.error_message,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]


@api_router.get("/documents/{document_id}")
async def get_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get details for a single document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "status": doc.status,
        "page_count": doc.page_count or 0,
        "chunk_count": doc.chunk_count or 0,
        "error_message": doc.error_message,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@api_router.delete("/documents/{document_id}")
async def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a document and all its chunks (cascade)."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted successfully."}


@api_router.post("/search")
async def search_documents(request: SearchRequest, db: Session = Depends(get_db)):
    """Semantic search using pgvector cosine similarity."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    # Embed the query using 'query: ' prefix
    query_vector = embed_query(request.query)

    # pgvector cosine distance search using the <=> operator
    results = db.execute(
        text(
            """
            SELECT
                dc.id,
                dc.document_id,
                dc.chunk_index,
                dc.text_content,
                d.filename,
                (dc.embedding <=> CAST(:query_vec AS vector)) AS distance
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE d.status = 'ready'
            ORDER BY dc.embedding <=> CAST(:query_vec AS vector)
            LIMIT :lim
            """
        ),
        {"query_vec": str(query_vector), "lim": request.limit},
    ).fetchall()

    return {
        "query": request.query,
        "results": [
            {
                "chunk_id": str(row.id),
                "document_id": str(row.document_id),
                "filename": row.filename,
                "chunk_index": row.chunk_index,
                "text": row.text_content,
                "score": round(1 - row.distance, 4),  # convert distance to similarity
            }
            for row in results
        ],
    }


@api_router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check – verifies the API and database are reachable."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "ok",
        "database": db_status,
        "model": settings.EMBEDDING_MODEL,
    }
