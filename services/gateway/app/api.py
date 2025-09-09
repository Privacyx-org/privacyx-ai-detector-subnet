import os, time, base64
from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, HttpUrl
import httpx
from .deps import require_api_key
from .qos import is_eligible

router = APIRouter()
SCHEDULER_URL = os.getenv("SCHEDULER_URL", "http://scheduler:9090")

# (optionnel) timeouts côté gateway -> scheduler
TIMEOUT_IMAGE_CLIENT_S = float(os.getenv("TIMEOUT_IMAGE_MS", "20000")) / 1000.0
TIMEOUT_VIDEO_CLIENT_S = float(os.getenv("TIMEOUT_VIDEO_MS", "30000")) / 1000.0

class ImageReq(BaseModel):
    image_b64: Optional[str] = None
    source_url: Optional[HttpUrl] = None
    return_explanation: bool = False
    client_ref: Optional[str] = None

class VideoReq(BaseModel):
    video_url: HttpUrl
    max_duration_sec: int = 6
    sampling: str = "keyframes"
    client_ref: Optional[str] = None

@router.get("/health")
async def health():
    async with httpx.AsyncClient(timeout=2.0) as cx:
        r = await cx.get(f"{SCHEDULER_URL}/health")
        r.raise_for_status()
        sched = r.json()
    return {"gateway_status": "ok", **sched}

@router.get("/qos/eligibility")
async def qos_eligibility(address: str, threshold_wei: int | None = None, x_api_key: str = Header(None)):
    require_api_key(x_api_key)
    try:
        ok, bal = is_eligible(address, threshold_wei)
        return {
            "address": address,
            "eligible": ok,
            "balance_wei": str(bal),
            "threshold_wei": str(threshold_wei) if threshold_wei is not None else None,
        }
    except Exception as e:
        raise HTTPException(500, f"qos check error: {e}")

async def _fetch_as_data_url(url: str) -> str:
    # Suivre les redirections (picsum, etc.)
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as cx:
        r = await cx.get(url)
        r.raise_for_status()
        ct = r.headers.get("content-type", "image/jpeg")
        b64 = base64.b64encode(r.content).decode()
        return f"data:{ct};base64,{b64}"

@router.post("/detect/image")
async def detect_image(
    body: ImageReq,
    x_api_key: str = Header(None),
    x_prvx_address: str | None = Header(default=None),
):
    require_api_key(x_api_key)
    if not (body.image_b64 or body.source_url):
        raise HTTPException(400, "image_b64 or source_url required")

    payload = body.model_dump()
    # Convertir source_url -> data URL pour les mineurs
    if body.source_url and not body.image_b64:
        payload["image_b64"] = await _fetch_as_data_url(str(body.source_url))
        payload["source_url"] = None

    # Injection priorité PRVX si adresse fournie et éligible
    if x_prvx_address:
        try:
            ok, _bal = is_eligible(x_prvx_address, None)
            payload["priority"] = bool(ok)
            payload["prvx_address"] = x_prvx_address
        except Exception:
            payload["priority"] = False

    t0 = time.perf_counter()
    async with httpx.AsyncClient(timeout=TIMEOUT_IMAGE_CLIENT_S) as cx:
        r = await cx.post(f"{SCHEDULER_URL}/dispatch/image", json=payload)
        r.raise_for_status()
        result = r.json()
    result["latency_ms"] = int((time.perf_counter() - t0) * 1000)
    p = result.get("consensus_prob", 0.5)
    result["label"] = "ai_likely" if p >= 0.8 else ("ai_unlikely" if p <= 0.2 else "uncertain")
    if x_prvx_address:
        result["prvx_address"] = x_prvx_address
    return result

@router.post("/detect/video")
async def detect_video(
    body: VideoReq,
    x_api_key: str = Header(None),
    x_prvx_address: str | None = Header(default=None),
):
    require_api_key(x_api_key)

    # model_dump() peut laisser video_url en type Url -> cast explicite pour JSON
    payload = body.model_dump()
    payload["video_url"] = str(body.video_url)

    if x_prvx_address:
        try:
            ok, _bal = is_eligible(x_prvx_address, None)
            payload["priority"] = bool(ok)
            payload["prvx_address"] = x_prvx_address
        except Exception:
            payload["priority"] = False

    t0 = time.perf_counter()
    async with httpx.AsyncClient(timeout=TIMEOUT_VIDEO_CLIENT_S) as cx:
        r = await cx.post(f"{SCHEDULER_URL}/dispatch/video", json=payload)
        r.raise_for_status()
        result = r.json()
    result["latency_ms"] = int((time.perf_counter() - t0) * 1000)
    p = result.get("consensus_prob", 0.5)
    result["label"] = "ai_likely" if p >= 0.8 else ("ai_unlikely" if p <= 0.2 else "uncertain")
    if x_prvx_address:
        result["prvx_address"] = x_prvx_address
    return result

