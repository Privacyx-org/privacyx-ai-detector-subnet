#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
if lsof -nP -iTCP:7070 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port 7070 déjà occupé"; exit 1
fi
uvicorn services.gateway.app.main:app \
  --host 127.0.0.1 --port 7070 \
  --env-file .env
