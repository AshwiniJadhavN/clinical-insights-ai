#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
	echo "Missing .env file. Copy .env.example to .env and set DATABASE_URL and POSTGRES_PASSWORD before running Docker Compose." >&2
	exit 1
fi

docker compose up --build -d
docker compose ps
