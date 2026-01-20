# backend/utils.py

import io
from typing import Optional

import pdfplumber
from docx import Document


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extrae texto de todo el PDF.
    """
    text_chunks = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_chunks.append(page_text)

    full_text = "\n".join(text_chunks)
    return full_text


def _extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extrae texto de todo el archivo DOCX.
    """
    file_stream = io.BytesIO(file_bytes)
    doc = Document(file_stream)

    paragraphs = [p.text for p in doc.paragraphs if p.text]
    full_text = "\n".join(paragraphs)

    return full_text


def extract_text(file_bytes: bytes, filename: Optional[str]) -> str:
    """
    Función principal de extracción de texto.
    Decide si el archivo es PDF o DOCX según la extensión del filename.
    """
    if not filename:
        raise ValueError("No se pudo determinar el tipo de archivo (filename vacío).")

    lower_name = filename.lower()

    if lower_name.endswith(".pdf"):
        return _extract_text_from_pdf(file_bytes)

    if lower_name.endswith(".docx"):
        return _extract_text_from_docx(file_bytes)

    raise ValueError("Formato de archivo no soportado. Usa PDF o DOCX.")