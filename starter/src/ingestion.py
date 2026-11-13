"""Read and normalize source data."""
import re
import unicodedata
from pathlib import Path

from pypdf import PdfReader

from .models import DocumentPage


def load_pdf(path: Path, document_id: str, source: str) -> list[DocumentPage]:
    """Extract each physical page; preserve page number and source."""
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    reader = PdfReader(str(path))
    pages: list[DocumentPage] = []
    for page_num, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        cleaned = normalize_text(raw_text)
        metadata = {
            "pdf_path": str(path),
            "page_index": page_num,
            "source": source,
            "has_text": bool(cleaned.strip()),
        }
        pages.append(
            DocumentPage(
                document_id=document_id,
                source=source,
                page=page_num,
                text=cleaned,
                metadata=metadata,
            )
        )
    return pages


def normalize_text(text: str) -> str:
    """Normalize Unicode and whitespace while keeping paragraph structure."""
    if not text:
        return ""

    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"\u00A0", " ", normalized)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r" *\n *", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    normalized = normalized.strip()
    return normalized
