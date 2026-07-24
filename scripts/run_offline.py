#!/usr/bin/env python3
from pathlib import Path
import os
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

env = os.environ.copy()
env.setdefault("DATABASE_URL", "sqlite:///./data/clinical_insights.db")
env.setdefault("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")
env.setdefault("UPLOAD_DIRECTORY", "./data/uploads")
env.setdefault("SAMPLE_DOCS_DIRECTORY", "./data/sample_docs")
env.setdefault("MOCK_LLM", "true")
env.setdefault("PORT", "8000")

Path("./data/chroma_db").mkdir(parents=True, exist_ok=True)
Path("./data/uploads").mkdir(parents=True, exist_ok=True)

command = [
    sys.executable,
    "-m",
    "uvicorn",
    "backend.main:app",
    "--host",
    "0.0.0.0",
    "--port",
    env["PORT"],
    "--reload",
]

print("Starting offline demo service...")
process = subprocess.Popen(command, env=env)

def wait_for_health(url: str, timeout: int = 30, interval: float = 0.5) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=3) as response:
                if response.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(interval)
    return False

health_url = f"http://127.0.0.1:{env['PORT']}/health"
if not wait_for_health(health_url):
    print("ERROR: Offline service did not become healthy in time.")
    process.terminate()
    process.wait(timeout=5)
    sys.exit(1)

print(f"Offline service is ready at http://127.0.0.1:{env['PORT']}")
print("Open http://127.0.0.1:8000/docs to inspect the API.")

try:
    process.wait()
except KeyboardInterrupt:
    print("Stopping offline demo service...")
    process.terminate()
    process.wait()