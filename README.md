# PrivacyX AI Detector Subnet (Local Dev)

Stable local setup for a PoC **Gateway (FastAPI)** + **Scheduler** + **Miners (stub)**.  
This supersedes the previous Docker-first quickstart. Docker can still be kept under `docs/docker.md`.

---

## Overview

- **Gateway (FastAPI)** — Public API that accepts image/video detection requests and forwards to the scheduler.  
  Default: `http://127.0.0.1:7070`
- **Scheduler** — Simple round-robin dispatcher to one or more **miners**.  
  Default: `http://127.0.0.1:7080`
- **Miners (stub)** — Lightweight inference stubs you can later replace with your ONNX/PyTorch model.  
  Defaults: `http://127.0.0.1:6061`, `http://127.0.0.1:6062`

> QoS (PRVX on-chain) is **disabled** by default for local dev. You can enable it when needed.

---

## Requirements

- Python 3.11+ (3.12 OK)
- macOS/Linux (Windows WSL ok)
- `curl` + `jq` for quick tests

---

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
Edit .env as needed. Minimal dev example:

ini
Copy code
API_KEYS=dev
SCHEDULER_URL=http://127.0.0.1:7080
DISABLE_QOS=1

# Scheduler → Miners
MINER_URLS=http://127.0.0.1:6061,http://127.0.0.1:6062
SCHEDULER_PORT=7080
Run (4 terminals)
Terminal D — Miner 1

bash
Copy code
source .venv/bin/activate
./run-miner.sh 6061
Terminal E — Miner 2

bash
Copy code
source .venv/bin/activate
./run-miner.sh 6062
Terminal A — Scheduler

bash
Copy code
source .venv/bin/activate
./run-scheduler.sh
Terminal B — Gateway

bash
Copy code
source .venv/bin/activate
./run-gateway.sh
Quick tests
Health

bash
Copy code
curl -s http://127.0.0.1:7080/health | jq .
curl -s -H 'x-api-key: dev' http://127.0.0.1:7070/v1/health | jq .
Image (URL)

bash
Copy code
curl -sS -X POST http://127.0.0.1:7070/v1/detect/image \
  -H 'x-api-key: dev' -H 'Content-Type: application/json' \
  -d '{"source_url":"https://upload.wikimedia.org/wikipedia/commons/3/3a/Cat03.jpg"}' | jq .
Image (base64)

bash
Copy code
IMG64="$(curl -s https://httpbin.org/image/png | base64)"
curl -sS -X POST http://127.0.0.1:7070/v1/detect/image \
  -H 'x-api-key: dev' -H 'Content-Type: application/json' \
  --data "{\"image_b64\":\"data:image/png;base64,${IMG64}\"}" | jq .
Video

bash
Copy code
curl -sS -X POST http://127.0.0.1:7070/v1/detect/video \
  -H 'x-api-key: dev' -H 'Content-Type: application/json' \
  -d '{"video_url":"https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"}' | jq .
Round-robin check

bash
Copy code
for i in {1..6}; do
  curl -sS -X POST http://127.0.0.1:7070/v1/detect/image \
    -H 'x-api-key: dev' -H 'Content-Type: application/json' \
    -d '{"source_url":"https://upload.wikimedia.org/wikipedia/commons/3/3a/Cat03.jpg"}' \
  | jq -r '.miner_url'
done
Endpoints
Gateway
GET /v1/health → {"gateway_status":"ok","status":"ok","miners":[...]}

POST /v1/detect/image

Body: { "source_url": "https://...", OR "image_b64": "data:image/...;base64,..." }

POST /v1/detect/video

Body: { "video_url": "https://..." }

GET /v1/qos/eligibility?address=0x...
Use only when QoS enabled (see ENV).

Scheduler
GET /health → {"status":"ok","miners":[...]}

POST /dispatch/image → forwards JSON to miner POST /infer/image (round-robin)

POST /dispatch/video → forwards JSON to miner POST /infer/video (round-robin)

Miners (stub)
GET /health

POST /infer/image → returns stub detections

POST /infer/video → returns stub detections

Environment variables
Gateway

API_KEYS — comma-separated list of accepted API keys (e.g. dev or dev,another_key).

SCHEDULER_URL — scheduler URL (default http://127.0.0.1:7080).

DISABLE_QOS — set to 1 to bypass PRVX checks in dev.

QoS (optional)

PRVX_RPC_URL — EVM RPC URL

PRVX_TOKEN_ADDRESS — ERC-20 token address

PRVX_QOS_THRESHOLD_WEI — min balance in wei

Scheduler

MINER_URLS — comma-separated list of miner base URLs (e.g. http://127.0.0.1:6061,http://127.0.0.1:6062)

SCHEDULER_PORT — port to bind (default 7080)

Replacing the stubs
Replace services/miner/app/main.py with your real ONNX/PyTorch inference.

Keep the same request/response shapes for seamless gateway/scheduler integration.

If you need weighted routing, add weights in the scheduler and change the round-robin to a weighted pick.

Troubleshooting
401 invalid api key → Header x-api-key must match API_KEYS.

500 PRVX RPC or token not configured → In dev, set DISABLE_QOS=1.
For real QoS, set PRVX_* variables.

404 .../dispatch/ from gateway* → Your scheduler isn’t exposing those routes. Start ./run-scheduler.sh.

500 from scheduler when posting video → Ensure it uses req.model_dump(mode="json") (fixed in this repo).

Port already in use →
lsof -tiTCP:6061,6062,7070,7080 -sTCP:LISTEN | xargs -I {} kill -9 {} 2>/dev/null || true

Contributing
Keep .env local; only commit .env.example.

Prefer small helper scripts (run-*.sh) and explicit env vars.

Update this README when gateway/scheduler/miner contracts change.

