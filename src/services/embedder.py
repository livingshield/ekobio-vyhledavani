from sentence_transformers import SentenceTransformer
import os

# Globální instance pro zamezení opakovaného načítání modelu do paměti (Singleton pattern)
_model = None

def get_model():
    global _model
    if _model is None:
        # Používáme multilingual-e5-small, který je skvělý pro češtinu a produkuje 384-dimenzionální vektory.
        # POZOR: V modelech.py jsme definovali Vector(768). Pro e5-small musíme použít 384, nebo přepnout na base/large (768).
        # Zde načteme E5-base, který má 768 dimenzí, aby to sedělo na DB schéma.
        model_name = os.environ.get("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
        _model = SentenceTransformer(model_name)
    return _model

def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Vygeneruje vektorové embeddingy pro seznam chunků.
    """
    if not texts:
        return []
        
    model = get_model()
    # Modely rodiny E5 vyžadují specifický prefix pro dokumenty v indexu
    prefixed_texts = [f"passage: {t}" for t in texts]
    
    # normalize_embeddings=True je doporučeno pro cosine similarity vyhledávání
    embeddings = model.encode(prefixed_texts, normalize_embeddings=True)
    
    return embeddings.tolist()
