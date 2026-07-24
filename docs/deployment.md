# Deployment

This project includes local Python and Docker Compose run paths for demonstration and development.

## Local Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
scripts/run_local.sh
```

Open `http://localhost:8000/docs`.

`scripts/run_local.sh` defaults to `MOCK_LLM=true`, which removes the external model-key dependency for local demos. Startup can still fail if local runtime dependencies are unavailable.

## Docker

```bash
scripts/build_image.sh
docker run --rm -p 8000:8000 clinical-insights-ai:local
```

## Docker Compose

```bash
scripts/deploy_local.sh
```

Check health:

```bash
curl http://localhost:8000/health
```

Docker Compose also runs with `MOCK_LLM=true` by default for repeatable local checks.

## Configuration

The Compose setup includes PostgreSQL so the API can run with a database-backed local environment. For lightweight local Python runs, `scripts/run_local.sh` defaults to SQLite. To exercise a live model provider, set `MOCK_LLM=false`, `DATABASE_URL`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY` through environment variables.
