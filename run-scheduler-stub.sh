#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
python - <<'PY'
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()
@app.get("/health")
def health(): return {"status": "ok"}

class ImageReq(BaseModel):
    source_url: str | None = None
    image_b64: str | None = None

@app.post("/dispatch/image")
async def dispatch_image(req: ImageReq):
    return {"ok": True, "type": "image", "received": req.model_dump(),
            "detections": [{"label": "stub-cat", "score": 0.99}]}

class VideoReq(BaseModel):
    video_url: str | None = None

@app.post("/dispatch/video")
async def dispatch_video(req: VideoReq):
    return {"ok": True, "type": "video", "received": req.model_dump(),
            "detections": [{"label": "stub-bunny", "score": 0.95}]}

uvicorn.run(app, host="127.0.0.1", port=7080)
PY
