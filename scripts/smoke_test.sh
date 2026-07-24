#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python3}"

"${PYTHON_BIN}" - <<'PY'
from fastapi.testclient import TestClient
from backend.main import create_app

app = create_app()
client = TestClient(app)

live_response = client.get('/health/live')
assert live_response.status_code == 200, live_response.text

health_response = client.get('/health')
assert health_response.status_code == 200, health_response.text

print('Smoke test passed: /health/live and /health responded successfully.')
PY
