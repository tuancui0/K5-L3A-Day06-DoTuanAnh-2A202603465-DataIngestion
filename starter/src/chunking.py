"""Implement fixed-size and structure-aware chunking."""
import re

from .models import Chunk, DocumentPage


def _make_chunk(page: DocumentPage, chunk_index: int, text: str, metadata: dict | None = None) -> Chunk:
    chunk_id = f"{page.document_id}:{page.page}:{chunk_index}"
    chunk_meta = {"source": page.source, "page": page.page, **(metadata or {}), **page.metadata}
    return Chunk(
        chunk_id=chunk_id,
        document_id=page.document_id,
        source=page.source,
        page=page.page,
        text=text.strip(),
        metadata=chunk_meta,
    )


def fixed_size(page: DocumentPage, size: int, overlap: int) -> list[Chunk]:
    """Split text into overlapping windows while preserving traceability."""
    text = page.text.strip()
    if not text:
        return []

    if overlap >= size:
        raise ValueError("Overlap must be smaller than chunk size.")

    chunks: list[Chunk] = []
    start = 0
    index = 0
    while start < len(text):
        end = min(len(text), start + size)
        segment = text[start:end].strip()
        if not segment:
            break
        chunks.append(_make_chunk(page, index, segment, {"chunking": "fixed_size", "size": size, "overlap": overlap}))
        if end >= len(text):
            break
        start += max(1, size - overlap)
        index += 1
    return chunks


def by_paragraph(page: DocumentPage, max_size: int) -> list[Chunk]:
    """Group paragraphs, splitting oversized paragraphs while keeping metadata."""
    text = page.text.strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[Chunk] = []
    chunk_index = 0
    for paragraph in paragraphs:
        if len(paragraph) <= max_size:
            chunks.append(_make_chunk(page, chunk_index, paragraph, {"chunking": "by_paragraph", "max_size": max_size}))
            chunk_index += 1
            continue

        words = paragraph.split()
        current = []
        current_len = 0
        for word in words:
            next_len = current_len + len(word) + (1 if current else 0)
            if current and next_len > max_size:
                chunks.append(_make_chunk(page, chunk_index, " ".join(current), {"chunking": "by_paragraph", "max_size": max_size}))
                chunk_index += 1
                current = [word]
                current_len = len(word)
            else:
                current.append(word)
                current_len = next_len

        if current:
            chunks.append(_make_chunk(page, chunk_index, " ".join(current), {"chunking": "by_paragraph", "max_size": max_size}))
            chunk_index += 1
    return chunks
