#!/usr/bin/env bash
set -euo pipefail

echo "# Scheduler health"
curl -s http://127.0.0.1:7080/health | jq .

echo "# Gateway health"
curl -s -H 'x-api-key: dev' http://127.0.0.1:7070/v1/health | jq .

echo "# Image URL"
curl -sS -X POST http://127.0.0.1:7070/v1/detect/image \
  -H 'x-api-key: dev' -H 'Content-Type: application/json' \
  -d '{"source_url":"https://upload.wikimedia.org/wikipedia/commons/3/3a/Cat03.jpg"}' | jq .

echo "# Video URL"
curl -sS -X POST http://127.0.0.1:7070/v1/detect/video \
  -H 'x-api-key: dev' -H 'Content-Type: application/json' \
  -d '{"video_url":"https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"}' | jq .

echo "# Round-robin (4 requests)"
for i in {1..4}; do
  curl -sS -X POST http://127.0.0.1:7070/v1/detect/image \
    -H 'x-api-key: dev' -H 'Content-Type: application/json' \
    -d '{"source_url":"https://upload.wikimedia.org/wikipedia/commons/3/3a/Cat03.jpg"}' \
  | jq -r '.miner_url'
done
