from sentence_transformers import SentenceTransformer
from src.config import settings

# Global singleton to avoid reloading the model on every request
_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate vector embeddings for document chunks.
    Uses 'passage: ' prefix as required by E5 models for documents.
    """
    if not texts:
        return []

    model = get_model()
    prefixed_texts = [f"passage: {t}" for t in texts]
    embeddings = model.encode(prefixed_texts, normalize_embeddings=True)
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """
    Generate a vector embedding for a search query.
    Uses 'query: ' prefix as required by E5 models for queries.
    """
    model = get_model()
    embedding = model.encode(
        [f"query: {query}"], normalize_embeddings=True
    )
    return embedding[0].tolist()
