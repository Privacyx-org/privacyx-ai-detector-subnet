#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-6061}"
# Lance l'app FastAPI définie dans services/miner/app/api.py
exec uvicorn services.miner.app.api:app --host 0.0.0.0 --port "${PORT}"
