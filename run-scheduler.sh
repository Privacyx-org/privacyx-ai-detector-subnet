#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate

# Exporter les variables de .env (si présent)
set -a
[ -f .env ] && source .env
set +a

export PYTHONUNBUFFERED=1
uvicorn services.scheduler.app.main:app \
  --host 127.0.0.1 \
  --port "${SCHEDULER_PORT:-7080}"
