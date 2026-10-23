FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip==24.0 \
    && pip install -r requirements.txt

COPY backend ./backend
COPY alembic ./alembic
COPY config ./config
COPY data/.gitkeep ./data/.gitkeep
COPY data/sample_docs ./data/sample_docs

RUN useradd --create-home --shell /bin/bash appuser \
    && mkdir -p /app/data/uploads /app/data/chroma_db \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
