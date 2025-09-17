#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate

# Exporter les variables de .env (si présent)
set -a
[ -f .env ] && source .env
set +a

PORT="${1:-6061}"
uvicorn services.miner.app.main:app --host 127.0.0.1 --port "$PORT"
