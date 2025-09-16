# PrivacyX AI Detector Subnet (Local Dev)

Stable local setup for a PoC **Gateway (FastAPI)** + **Scheduler**.  
This replaces the older Docker-first quickstart (you can keep Docker as legacy if you want).

---

## Overview

- **Gateway (FastAPI)** — public API that accepts image/video detection requests.
- **Scheduler (stub by default)** — receives dispatch requests from the gateway and returns stub detections.
- You can later replace the stub with your real scheduler/miner/validator stack.

**Default ports**

- Gateway: `http://127.0.0.1:7070`
- Scheduler (stub): `http://127.0.0.1:7080`

---

## Requirements

- Python 3.11+ (3.12 OK)
- macOS/Linux (Windows WSL is fine)
- `curl` for quick tests

---

## Setup

Create and activate a virtualenv, then install deps:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
Create a .env from the example and edit it:

bash
Copy code
cp .env.example .env
Minimal dev config (you can paste to overwrite .env now):

bash
Copy code
printf '%s\n' \
'API_KEYS=dev' \
'SCHEDULER_URL=http://127.0.0.1:7080' \
'DISABLE_QOS=1' > .env
Notes

API_KEYS is the variable the gateway actually uses (comma-separated list allowed).

DISABLE_QOS=1 bypasses PRVX eligibility checks in local dev.

If you enable QoS, also set:

PRVX_RPC_URL

PRVX_TOKEN_ADDRESS

PRVX_QOS_THRESHOLD_WEI (default: 1000000000000000000000)

If needed, make the helper scripts executable:

bash
Copy code
chmod +x run-scheduler-stub.sh run-gateway.sh
Run (two terminals)
Terminal A — scheduler stub (port 7080):

bash
Copy code
./run-scheduler-stub.sh
Terminal B — gateway (port 7070):

bash
Copy code
./run-gateway.sh
You should see Uvicorn running on http://127.0.0.1:7070.

Quick tests
Health
bash
Copy code
curl -i -H 'x-api-key: dev' http://127.0.0.1:7070/v1/health
Detect image (URL)
bash
Copy code
curl -i -H 'x-api-key: dev' -H 'Content-Type: application/json' \
  --data '{"source_url":"https://upload.wikimedia.org/wikipedia/commons/3/3a/Cat03.jpg"}' \
  http://127.0.0.1:7070/v1/detect/image
Detect image (base64 Data URL)
bash
Copy code
IMG64="$(curl -s https://httpbin.org/image/png | base64)"
curl -i -H 'x-api-key: dev' -H 'Content-Type: application/json' \
  --data "{\"image_b64\":\"data:image/png;base64,${IMG64}\"}" \
  http://127.0.0.1:7070/v1/detect/image
Detect video
bash
Copy code
curl -i -H 'x-api-key: dev' -H 'Content-Type: application/json' \
  --data '{"video_url":"https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"}' \
  http://127.0.0.1:7070/v1/detect/video
QoS (only when enabled)
bash
Copy code
curl -i -H 'x-api-key: dev' \
  'http://127.0.0.1:7070/v1/qos/eligibility?address=0xYOURADDRESS'
API Reference (Gateway)
Base URL: http://127.0.0.1:7070
Auth: header x-api-key: <one of API_KEYS>

GET /v1/health
Returns gateway + scheduler health.

Response:

json
Copy code
{"gateway_status":"ok","status":"ok"}
POST /v1/detect/image
Headers: x-api-key

Body (JSON): one of

{"source_url":"https://..."}

{"image_b64":"data:image/<type>;base64,<...>"}

Optional header (when QoS enabled): X-PRVX-Address: 0x...

Example response:

json
Copy code
{
  "ok": true,
  "type": "image",
  "detections": [{"label": "stub-cat", "score": 0.99}],
  "latency_ms": 12,
  "label": "uncertain"
}
POST /v1/detect/video
Headers: x-api-key

Body (JSON): {"video_url":"https://..."}

Optional header (when QoS enabled): X-PRVX-Address: 0x...

Response shape mirrors /v1/detect/image.

GET /v1/qos/eligibility?address=<0x...>
Returns eligibility based on PRVX balance when QoS is configured.

In dev, set DISABLE_QOS=1 to bypass this.

Environment variables
API_KEYS — comma-separated list of accepted API keys (e.g. dev or dev,another_key).

SCHEDULER_URL — URL for the scheduler service (stub by default).

DISABLE_QOS — set to 1 to bypass PRVX checks in dev.

(QoS) PRVX_RPC_URL — EVM RPC; PRVX_TOKEN_ADDRESS — ERC-20 address; PRVX_QOS_THRESHOLD_WEI — threshold in wei.

Replacing the stub with your real scheduler
The gateway calls the scheduler:

GET {SCHEDULER_URL}/health → expects {"status":"ok"}

POST {SCHEDULER_URL}/dispatch/image with JSON including one of:

image_b64 (full Data URL) or source_url

POST {SCHEDULER_URL}/dispatch/video with JSON including:

video_url

Expected 200 response example:

json
Copy code
{
  "ok": true,
  "type": "image|video",
  "detections": [{"label":"...", "score":0.95}]
}
Just point SCHEDULER_URL to your real service and restart ./run-gateway.sh.

Troubleshooting
401 invalid api key
Ensure header x-api-key matches a value in API_KEYS.

500 PRVX RPC or token not configured / QoS errors
For dev, set DISABLE_QOS=1. For real QoS, provide PRVX_RPC_URL, PRVX_TOKEN_ADDRESS, PRVX_QOS_THRESHOLD_WEI.

404 .../dispatch/* from gateway
Your scheduler isn’t exposing those routes. Use the stub or implement the endpoints.

Port already in use
Check: lsof -nP -iTCP:7070 -sTCP:LISTEN (or 7080) and kill the lingering process.

Legacy (Docker)
The previous Docker-first flow can be kept as a separate doc (e.g. docs/docker.md) for CI or team parity.
This README focuses on the Python-first local setup because it’s generally more stable on macOS (avoids Docker Desktop resets/DNS quirks).

Contributing
Keep .env local and untracked; only commit .env.example.

Prefer small scripts (run-*.sh) and explicit env vars.

Update this README when gateway/scheduler contracts change.

