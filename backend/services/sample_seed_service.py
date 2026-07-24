"""
Startup seeding for zero-friction demos.
"""

from pathlib import Path

from backend.rag.chunker import chunk_text
from backend.rag.embedder import EmbedderProtocol
from backend.rag.retriever import RetrieverProtocol
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def seed_sample_documents(
    embedder: EmbedderProtocol,
    retriever: RetrieverProtocol,
    sample_dir: str,
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    if retriever.count() > 0:
        return

    path = Path(sample_dir)
    if not path.exists():
        logger.info("Sample seed skipped: directory does not exist")
        return

    seeded = 0
    for sample_file in sorted(path.glob("*.txt")):
        text = sample_file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        chunks = chunk_text(
            text=text,
            doc_id=f"sample-{sample_file.stem}",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        if not chunks:
            continue
        embeddings = embedder.embed_batch([chunk.text for chunk in chunks])
        retriever.index_chunks(chunks, embeddings, sample_file.name)
        seeded += len(chunks)

    logger.info("Sample seed complete: chunks=%d", seeded)
