# services/miner/app/api.py
import os
import base64
import io
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

import numpy as np
from PIL import Image
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

MODEL_IMPL = os.getenv("MODEL_IMPL", "stub").lower()

# ---------- Impl selection ----------
DetectorType = Any
_detector: Optional[DetectorType] = None

def _build_detector() -> DetectorType:
    if MODEL_IMPL == "onnx":
        from services.miner.impl_onnx import OnnxDetector
        return OnnxDetector()
    else:
        class StubDetector:
            def detect_image(self, image_b64: str, return_explanation: bool = False) -> Dict[str, Any]:
                out = {"detections": [{"label": "stub", "score": 0.5}]}
                if return_explanation:
                    out["explanation"] = {"note": "stub implementation"}
                return out
        return StubDetector()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _detector
    _detector = _build_detector()
    yield
    _detector = None

app = FastAPI(lifespan=lifespan)

# ---------- Schemas ----------
class ImageReq(BaseModel):
    # Le gateway envoie normalement image_b64 (data URL). On tolère aussi source_url par sécurité.
    image_b64: Optional[str] = None
    source_url: Optional[HttpUrl] = None
    return_explanation: bool = False

class VideoReq(BaseModel):
    video_url: HttpUrl
    max_duration_sec: int = 6
    sampling: str = "keyframes"

# ---------- Utils ----------
def _url_to_data_url(url: str) -> str:
    import requests
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    content = resp.content
    # Devine un mimetype simple
    mime = "image/jpeg"
    if url.lower().endswith(".png"):
        mime = "image/png"
    elif url.lower().endswith(".webp"):
        mime = "image/webp"
    return f"data:{mime};base64,{base64.b64encode(content).decode()}"

# ---------- Routes ----------
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_impl": MODEL_IMPL,
        "has_detector": bool(_detector is not None),
    }

def _run_image_inference(body: ImageReq) -> Dict[str, Any]:
    if _detector is None:
        raise HTTPException(500, "detector not initialized")

    if not body.image_b64 and body.source_url:
        # tolérance : si le gateway n’a pas fait le b64, on le fait ici
        try:
            image_b64 = _url_to_data_url(str(body.source_url))
        except Exception as e:
            raise HTTPException(400, f"failed_to_fetch_source_url: {e}")
    elif body.image_b64:
        image_b64 = body.image_b64
    else:
        raise HTTPException(400, "image_b64 or source_url is required")

    try:
        return _detector.detect_image(
            image_b64=image_b64,
            return_explanation=body.return_explanation,
        )
    except Exception as e:
        raise HTTPException(500, f"onnx_error: {e}")

# Nouveau endpoint (notre préférence)
@app.post("/detect/image")
async def detect_image(body: ImageReq):
    return _run_image_inference(body)

# Endpoint legacy appelé par le scheduler/gateway actuel
@app.post("/infer/image")
async def infer_image(body: ImageReq):
    return _run_image_inference(body)

@app.post("/detect/video")
async def detect_video(body: VideoReq):
    # stub vidéo, identique à avant
    return {"detections": [{"label": "bunny", "score": 0.91}]}

