import pdfplumber

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extrahuje surový text ze všech stránek PDF dokumentu.
    Využívá pdfplumber, který je plně open-source (MIT) na rozdíl od PyMuPDF (AGPL).
    """
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Chyba při parsování PDF {file_path}: {e}")
        raise
    return text
