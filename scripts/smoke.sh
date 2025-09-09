#!/usr/bin/env bash
set -euo pipefail

API=http://localhost:8080
KEY=dev_key_123
VIP=0xfbe27f21157a60184fe223d2c8e54ea2032a8189

echo "# Health"
curl -s "$API/v1/health" | jq . || true

echo -e "\n# Non-VIP detect/image"
curl -sS -X POST "$API/v1/detect/image" \
  -H "x-api-key: $KEY" -H 'Content-Type: application/json' \
  -d '{"source_url":"https://picsum.photos/seed/smoke-nonvip/512.jpg"}' | jq .

echo -e "\n# VIP detect/image"
curl -sS -X POST "$API/v1/detect/image" \
  -H "x-api-key: $KEY" -H "x-prvx-address: $VIP" -H 'Content-Type: application/json' \
  -d '{"source_url":"https://picsum.photos/seed/smoke-vip/512.jpg"}' | jq .

echo -e "\n# QoS eligibility"
curl -sS "$API/v1/qos/eligibility?address=$VIP" -H "x-api-key: $KEY" | jq .
