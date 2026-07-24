#!/usr/bin/env python3
"""Check ChromaDB and PGVector for vector ID divergence."""

from __future__ import annotations

import argparse
import json

from sqlalchemy import text

from backend.config import get_settings
from backend.database.session import get_session_factory, init_db
from backend.retrieval.reconcile import reconcile_vector_ids


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    settings = get_settings()
    chroma_ids = _load_chroma_ids(settings.chroma_persist_directory, settings.chroma_collection_name)
    pgvector_ids = _load_pgvector_ids(settings.database_url)
    result = reconcile_vector_ids(chroma_ids, pgvector_ids)

    payload = {
        "passed": result.passed,
        "chroma_count": result.chroma_count,
        "pgvector_count": result.pgvector_count,
        "missing_in_pgvector": result.missing_in_pgvector,
        "missing_in_chroma": result.missing_in_chroma,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(
            f"passed={result.passed} chroma_count={result.chroma_count} "
            f"pgvector_count={result.pgvector_count}"
        )
        for key in ("missing_in_pgvector", "missing_in_chroma"):
            if payload[key]:
                print(f"{key}:")
                for item in payload[key]:
                    print(f" - {item}")
    return 0 if result.passed else 1


def _load_chroma_ids(persist_directory: str, collection_name: str) -> set[str]:
    import chromadb

    client = chromadb.PersistentClient(path=persist_directory)
    collection = client.get_or_create_collection(collection_name)
    result = collection.get(include=[])
    return {str(item) for item in result.get("ids", [])}


def _load_pgvector_ids(database_url: str) -> set[str]:
    init_db(database_url)
    with get_session_factory()() as session:
        rows = session.execute(
            text("SELECT id FROM documents WHERE embedding IS NOT NULL")
        )
        return {str(row.id) for row in rows}


if __name__ == "__main__":
    raise SystemExit(main())
