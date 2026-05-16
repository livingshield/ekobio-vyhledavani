import os
import time
from celery import Celery
from src.database import SessionLocal
from src.models import Document, DocumentChunk
from src.services.pdf_parser import extract_text_from_pdf
from src.services.chunker import chunk_text
from src.services.embedder import generate_embeddings

celery_app = Celery(
    "semantic_worker",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Prague",
    enable_utc=True,
)

@celery_app.task(bind=True, max_retries=3)
def process_document_task(self, document_id: str):
    """
    Background task to parse PDF, chunk text, and generate vector embeddings.
    """
    # TODO: Implement PDF extraction and chunking
    # TODO: Run text through sentence-transformers
    # TODO: Save vectors to Postgres
    print(f"Starting processing for document {document_id}")
    return {"status": "success", "document_id": document_id}
