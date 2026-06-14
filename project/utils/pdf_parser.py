import io
from PyPDF2 import PdfReader

def extract_text_from_pdf(path: str) -> str:
    text_chunks = []
    with open(path, 'rb') as fh:
        reader = PdfReader(fh)
        for page in reader.pages:
            try:
                text = page.extract_text() or ''
            except Exception:
                text = ''
            if text:
                text_chunks.append(text)
    return '\n'.join(text_chunks)
