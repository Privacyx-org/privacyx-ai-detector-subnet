# PrivacyX AI Detector Subnet

Subnet Bittensor pour la détection d'images/vidéos (PoC local avec gateway/scheduler/miners/validator).

## Services

- **gateway** : API FastAPI (port 8080)
- **scheduler** : sélectionne un comité de miners (port 9090)
- **validator** : agrège/valide (port 7070)
- **miners** : inference (port 6060 interne)

## Démarrage rapide

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
