"""
Text chunker: splits extracted document text into overlapping segments.

Why chunking matters for RAG:
  - LLMs have a limited context window — we cannot feed them an entire PDF
  - Chunks that are too large lose retrieval specificity
  - Chunks that are too small lose surrounding context needed for answers
  - Overlap at boundaries ensures clinical context is never silently split
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

DEFAULT_CHUNK_SIZE: int = 512
DEFAULT_CHUNK_OVERLAP: int = 64
MIN_CHUNK_SIZE: int = 50


@dataclass(frozen=True)
class TextChunk:
    """
    A single segment of extracted document text, ready for embedding.

    frozen=True enforces immutability — chunks are data-transfer objects.
    """

    text: str
    chunk_index: int
    start_char: int
    end_char: int
    doc_id: str
    char_count: int = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "char_count", len(self.text))


def chunk_text(
    text: str,
    doc_id: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    """
    Split document text into overlapping chunks for vector embedding.

    Raises:
        ValueError: if chunk_overlap >= chunk_size.
    """
    if not text or len(text.strip()) < MIN_CHUNK_SIZE:
        return []

    _validate_chunk_params(chunk_size, chunk_overlap)

    return list(_sliding_window(text.strip(), doc_id, chunk_size, chunk_overlap))


def chunk_text_streaming(
    text: str,
    doc_id: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> Iterator[TextChunk]:
    """Generator version of chunk_text for memory-efficient large-document processing."""
    if not text or len(text.strip()) < MIN_CHUNK_SIZE:
        return

    _validate_chunk_params(chunk_size, chunk_overlap)
    yield from _sliding_window(text.strip(), doc_id, chunk_size, chunk_overlap)


def _validate_chunk_params(chunk_size: int, chunk_overlap: int) -> None:
    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) must be less than "
            f"chunk_size ({chunk_size}). Current values would cause an infinite loop."
        )


def _sliding_window(
    text: str,
    doc_id: str,
    chunk_size: int,
    chunk_overlap: int,
) -> Iterator[TextChunk]:
    step = chunk_size - chunk_overlap

    for idx, start in enumerate(range(0, len(text), step)):
        end = min(start + chunk_size, len(text))
        segment = text[start:end].strip()

        if len(segment) < MIN_CHUNK_SIZE:
            break

        yield TextChunk(
            text=segment,
            chunk_index=idx,
            start_char=start,
            end_char=end,
            doc_id=doc_id,
        )
