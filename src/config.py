from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Database - support direct DATABASE_URL (e.g. Neon connection string)
    DATABASE_URL: Optional[str] = None

    # Fallback: individual Postgres vars
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "semantic_index"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Embedding model configuration
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-small"
    VECTOR_DIMENSIONS: int = 384

    # Upload directory for temporary PDF storage
    UPLOAD_DIR: str = "uploads"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def database_url(self) -> str:
        """Return DATABASE_URL if set directly, otherwise build from individual vars."""
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
