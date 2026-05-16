import uuid6
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from src.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid6.uuid7)
    filename = Column(String(255), nullable=False)
    status = Column(String(50), default="uploaded") # uploaded, processing, ready, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Full text search column
    search_vector = Column(TSVECTOR)

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid6.uuid7)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=False)
    
    # Vector embedding column (e.g. 768 dimensions for BGE/E5 base models)
    embedding = Column(Vector(768))
