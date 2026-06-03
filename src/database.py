from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from src.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create the pgvector extension and all tables if they don't exist."""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # Import models so Base.metadata knows about them
    from src import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
