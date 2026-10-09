"""
Raw text extraction from uploaded resume files.
Supports PDF and DOCX. Add more formats here as needed later.
"""
import os

import pdfplumber
from docx import Document


class UnsupportedFileTypeError(Exception):
    pass


def extract_text(file_path: str) -> str:
    """Dispatch to the right extractor based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return _extract_from_pdf(file_path)
    elif ext in (".docx",):
        return _extract_from_docx(file_path)
    elif ext == ".txt":
        return _extract_from_txt(file_path)
    else:
        raise UnsupportedFileTypeError(
            f"Unsupported resume file type '{ext}'. Use PDF, DOCX, or TXT."
        )


def _extract_from_pdf(file_path: str) -> str:
    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n".join(text_parts).strip()


def _extract_from_docx(file_path: str) -> str:
    document = Document(file_path)
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    # Also pull text out of tables (common in resumes with skill tables)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    paragraphs.append(cell.text)
    return "\n".join(paragraphs).strip()


def _extract_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()
