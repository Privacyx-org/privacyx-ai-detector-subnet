# PrivacyX — AI Detector Subnet (ONNX / CPU)

A full microservice stack (gateway → scheduler → miners) providing ONNX-based
image classification using a ResNet50 v2 model on CPU.

## Requirements

- Docker & Docker Compose v2
- (Optional) `jq` for pretty JSON output

## Project layout

services/
miner/
app/
api.py # FastAPI endpoints: /health, /info, /detect/image, /infer/image
impl_onnx.py # ONNX inference (CPU)
models/
detector.onnx # ONNX model (not versioned)
imagenet_classes.txt
Dockerfile.gateway
Dockerfile.scheduler
Dockerfile.miner
docker-compose.prod.yml
run-miner.sh

bash
Copy code

## Setup

1. Copy the environment file:
   ```bash
   cp .env.example .env
Key variables (defaults if unset):

API_KEYS (default: dev)

MODEL_IMPL=onnx

MODEL_PATH=/app/services/miner/models/detector.onnx

IMAGENET_LABELS_PATH=/app/services/miner/models/imagenet_classes.txt

DISABLE_QOS=1

Download model & labels:

bash
Copy code
mkdir -p services/miner/models
curl -L -o services/miner/models/detector.onnx \
  "https://media.githubusercontent.com/media/onnx/models/main/validated/vision/classification/resnet/model/resnet50-v2-7.onnx"
curl -L -o services/miner/models/imagenet_classes.txt \
  "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"
wc -l services/miner/models/imagenet_classes.txt   # should print 1000
Build & run
bash
Copy code
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps
Wait until the gateway container reports healthy.

Quick tests
Gateway health:

bash
Copy code
curl -s http://127.0.0.1:7070/v1/health | python -m json.tool
Image detection from URL:

bash
Copy code
curl -s http://127.0.0.1:7070/v1/detect/image \
  -H 'x-api-key: dev' -H 'content-type: application/json' \
  -d '{"source_url":"https://picsum.photos/seed/px/600/400","return_explanation":true}' \
  | python -m json.tool
Image detection with PRVX address:

bash
Copy code
curl -s http://127.0.0.1:7070/v1/detect/image \
  -H 'x-api-key: dev' \
  -H 'x-prvx-address: 0xYourAddress' \
  -H 'content-type: application/json' \
  -d '{"source_url":"https://picsum.photos/seed/px/600/400"}' \
  | python -m json.tool
Miner diagnostics
Miners are internal only. Use exec inside Docker to inspect:

bash
Copy code
docker compose -f docker-compose.prod.yml exec miner1 sh -lc 'curl -fsS http://localhost:6061/health'
docker compose -f docker-compose.prod.yml exec miner1 sh -lc 'curl -fsS http://localhost:6061/info'
If you prefer direct host access for debugging, you can expose ports:

yaml
Copy code
miner1:
  ports: ["6061:6061"]
miner2:
  ports: ["6062:6062"]
Updating the model
Replace services/miner/models/detector.onnx and restart miners:

bash
Copy code
docker compose -f docker-compose.prod.yml up -d --force-recreate --no-deps miner1 miner2
Performance notes
Default threading:

OMP_NUM_THREADS=1

ORT_NUM_THREADS=1

You can experiment with 2 if CPU has more cores:

yaml
Copy code
environment:
  - OMP_NUM_THREADS=2
  - ORT_NUM_THREADS=2
Useful endpoints
GET /health – service status

GET /info – runtime info (env vars, ONNX providers)

POST /detect/image or POST /infer/image – image classification
Request JSON:

json
Copy code
{
  "image_b64": "data:image/jpeg;base64,...",
  "return_explanation": true
}
or

json
Copy code
{
  "source_url": "https://example.com/image.jpg",
  "return_explanation": false
}
Versioning
Create and push a tag:

bash
Copy code
git tag -a vX.Y.Z -m "description"
git push origin vX.Y.Z
