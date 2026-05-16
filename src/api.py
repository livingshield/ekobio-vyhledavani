from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import uuid
from pydantic import BaseModel

from src.database import get_db
from src.models import Document
from src.worker import process_document_task

api_router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    limit: int = 5

@api_router.post("/documents", status_code=202)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a document to be indexed sementically."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    # Placeholder: Create record in DB
    new_doc = Document(filename=file.filename, status="uploaded")
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    # Trigger async processing
    process_document_task.delay(str(new_doc.id))
    
    return {"message": "Document uploaded successfully", "document_id": new_doc.id}

@api_router.get("/documents/{document_id}")
async def get_document_status(document_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get status of document processing."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"id": doc.id, "filename": doc.filename, "status": doc.status}

@api_router.post("/search")
async def search_documents(request: SearchRequest, db: Session = Depends(get_db)):
    """Hybrid search endpoint (Vector + Fulltext)."""
    # TODO: 1. Convert request.query to vector using sentence-transformers
    # TODO: 2. Query Postgres pgvector using L2/Cosine similarity
    # TODO: 3. Query Postgres TSVECTOR for lexical match
    # TODO: 4. Combine results (RRF)
    
    return {"query": request.query, "results": []}
