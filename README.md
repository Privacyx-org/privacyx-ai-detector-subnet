# PrivacyX AI Detector Subnet

Bittensor subnet for image/video detection (local PoC with gateway/scheduler/miners/validator).

## Services

- **gateway** : API FastAPI (port 8080)
- **scheduler** : selects a committee of miners (port 9090)
- **validator** : aggregate/validate (port 7070)
- **miners** : inference (internal port 6060)

## Quick start

```bash
docker compose up -d --build
curl -s http://localhost:8080/v1/health | jq .
curl -s http://localhost:9090/health | jq .

curl -sS -X POST http://localhost:8080/v1/detect/image \
  -H 'x-api-key: dev_key_123' -H 'Content-Type: application/json' \
  -d '{"source_url":"https://picsum.photos/seed/demo/512.jpg"}' | jq .

curl -sS -X POST http://localhost:8080/v1/detect/video \
  -H 'x-api-key: dev_key_123' -H 'Content-Type: application/json' \
  -d '{"video_url":"https://files.samplevideofiles.com/video123/mp4/720/big_buck_bunny_720p_5mb.mp4"}' | jq .

curl -s 'http://localhost:8080/v1/qos/eligibility?address=0xABC...' \
  -H 'x-api-key: dev_key_123' | jq .

```

## Model
The ONNX model file is not versioned (size > 100 MB). Place your model locally:
- Copy your template to `services/miner/models/detector.onnx`
- Or adjust `MODEL_PATH` via an env/volume Docker variable.

