def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    """
    Základní chunkovací algoritmus. 
    Rozdělí dlouhý text na překrývající se segmenty (okna) pro zachování sémantického kontextu.
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        
        # Pokud nekončíme na konci textu, zkusíme najít nejbližší konec věty
        if end < text_length:
            last_period = text.rfind('.', start, end)
            if last_period != -1 and last_period > start + (chunk_size // 2):
                end = last_period + 1
                
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
            
        start = end - overlap
        
    return chunks
