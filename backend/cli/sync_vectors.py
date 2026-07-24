#!/usr/bin/env python3
"""Backfill existing ChromaDB vectors into PGVector."""

from __future__ import annotations

import argparse

from backend.config import get_settings
from backend.database.session import get_session_factory, init_db
from backend.rag.chunker import TextChunk
from backend.rag.pgvector_retriever import PGVectorRetriever


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args()

    settings = get_settings()
    init_db(settings.database_url)
    pgvector = PGVectorRetriever(get_session_factory())

    import chromadb

    client = chromadb.PersistentClient(path=settings.chroma_persist_directory)
    collection = client.get_or_create_collection(settings.chroma_collection_name)
    total = collection.count()
    synced = 0

    for offset in range(0, total, args.batch_size):
        batch = collection.get(
            limit=args.batch_size,
            offset=offset,
            include=["documents", "embeddings", "metadatas"],
        )
        documents = batch.get("documents", [])
        embeddings = batch.get("embeddings", [])
        metadatas = batch.get("metadatas", [])

        chunks: list[TextChunk] = []
        for index, (document, metadata) in enumerate(zip(documents, metadatas)):
            chunk = TextChunk(
                text=document,
                chunk_index=int(metadata.get("chunk_index", index)),
                start_char=int(metadata.get("start_char", 0)),
                end_char=int(metadata.get("end_char", len(document))),
                doc_id=str(metadata.get("doc_id", f"backfill-{offset}-{index}")),
            )
            chunks.append(chunk)

        original_filename = "chroma_backfill"
        if metadatas:
            original_filename = str(metadatas[0].get("original_filename", original_filename))
        pgvector.index_chunks(chunks, embeddings, original_filename)
        synced += len(chunks)
        print(f"synced={synced}/{total}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
