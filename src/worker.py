from celery import Celery
from src.config import settings

# Initialize Celery app
celery_app = Celery(
    "semantic_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
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
