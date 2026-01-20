# backend/text_extractor.py

import io
from typing import Optional

# Para PDFs
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

# Para DOCX (opcional)
try:
    from docx import Document  # python-docx
except ImportError:
    Document = None


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extrae texto de un PDF usando PyPDF2.
    Devuelve string vacío si algo falla.
    """
    if PdfReader is None:
        # Librería no instalada: devolvemos vacío para no romper el backend
        return ""

    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for page in reader.pages:
            try:
                t = page.extract_text() or ""
            except Exception:
                t = ""
            pages_text.append(t)
        return "\n".join(pages_text)
    except Exception:
        return ""


def _extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extrae texto de un DOCX usando python-docx.
    Si no está instalado o algo falla, devolvemos texto decodificado simple.
    """
    if Document is None:
        # Fallback: intentar decodificar como texto plano
        try:
            return file_bytes.decode("utf-8")
        except Exception:
            return file_bytes.decode("latin-1", errors="ignore")

    try:
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text]
        return "\n".join(paragraphs)
    except Exception:
        try:
            return file_bytes.decode("utf-8")
        except Exception:
            return file_bytes.decode("latin-1", errors="ignore")


def extract_text_from_file(file_bytes: bytes, filename: Optional[str] = None) -> str:
    """
    Punto de entrada único que usa el motor de reglas.

    - Detecta la extensión por el nombre del archivo.
    - Si es PDF → usa PyPDF2.
    - Si es DOCX → usa python-docx.
    - En cualquier otro caso → intenta decodificar bytes como texto plano.
    """
    ext = ""
    if filename and "." in filename:
        ext = filename.lower().rsplit(".", 1)[-1]

    # Ruteo por tipo
    if ext == "pdf":
        return _extract_text_from_pdf(file_bytes)
    elif ext == "docx":
        return _extract_text_from_docx(file_bytes)
    else:
        # Fallback genérico: asumimos texto plano
        try:
            return file_bytes.decode("utf-8")
        except Exception:
            return file_bytes.decode("latin-1", errors="ignore")