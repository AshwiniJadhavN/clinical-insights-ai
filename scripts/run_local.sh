#!/usr/bin/env bash
set -euo pipefail

export DATABASE_URL="${DATABASE_URL:-sqlite:///./data/clinical_insights.db}"
export CHROMA_PERSIST_DIRECTORY="${CHROMA_PERSIST_DIRECTORY:-./data/chroma_db}"
export UPLOAD_DIRECTORY="${UPLOAD_DIRECTORY:-./data/uploads}"
export SAMPLE_DOCS_DIRECTORY="${SAMPLE_DOCS_DIRECTORY:-./data/sample_docs}"
export MOCK_LLM="${MOCK_LLM:-true}"

mkdir -p data/chroma_db data/uploads

exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}" --reload
