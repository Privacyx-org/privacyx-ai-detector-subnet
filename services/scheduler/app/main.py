import os, random
from typing import Optional, Any
from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
import httpx

COMMITTEE_SIZE_IMAGE = int(os.getenv("COMMITTEE_SIZE_IMAGE","5"))
COMMITTEE_SIZE_VIDEO = int(os.getenv("COMMITTEE_SIZE_VIDEO","7"))
VALIDATOR_URL = os.getenv("VALIDATOR_URL","http://validator:7070")
MINERS = [m.strip() for m in os.getenv("MINERS","http://miner:6060").split(",") if m.strip()]

app = FastAPI(title="PrivacyX Scheduler")
router = APIRouter()

class ImageReq(BaseModel):
    image_b64: Optional[str] = None
    source_url: Optional[str] = None
    return_explanation: bool = False
    client_ref: Optional[str] = None
    priority: bool = False
    prvx_address: Optional[str] = None

class VideoReq(BaseModel):
    video_url: str
    max_duration_sec: int = 6
    sampling: str = "keyframes"
    client_ref: Optional[str] = None
    priority: bool = False
    prvx_address: Optional[str] = None

@app.get("/health")
async def health():
    return {"status":"ok","miners_online":len(MINERS),"validators_online":1}

def _truthy(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, str):
        return v.strip().lower() in ("1","true","yes","y","on")
    return False

async def _dispatch_to_committee(typ:str, payload: dict):
    is_vip = _truthy(payload.get("priority", False))
    base_k = COMMITTEE_SIZE_IMAGE if typ=="image" else COMMITTEE_SIZE_VIDEO
    # VIP = comité maximum dispo pour bien visualiser l'effet
    k = len(MINERS) if is_vip else min(len(MINERS), base_k)
    committee = random.sample(MINERS, min(k, len(MINERS)))
    probs, latencies = [], []
    async with httpx.AsyncClient(timeout=15.0) as cx:
        for m in committee:
            try:
                r = await cx.post(
                    f"{m}/infer",
                    json={"type":typ, **payload, "deadline_ms": (2500 if is_vip else 4000)}
                )
                j = r.json()
                probs.append(float(j.get("prob",0.5)))
                latencies.append(int(j.get("inference_ms",0)))
            except Exception:
                probs.append(0.5); latencies.append(9999)
    async with httpx.AsyncClient(timeout=5.0) as cx:
        vr = await cx.post(f"{VALIDATOR_URL}/assess", json={
            "probs": probs, "latencies_ms": latencies, "z_threshold": 2.0, "trim_ratio": 0.2
        })
        vr.raise_for_status()
        cons = vr.json()
    cons["committee"] = committee
    cons["priority"] = is_vip
    return cons

@router.post("/dispatch/image")
async def dispatch_image(body: ImageReq):
    if not body.image_b64:
        raise HTTPException(400,"image_b64 required (gateway converts source_url)")
    return await _dispatch_to_committee("image", body.model_dump())

@router.post("/dispatch/video")
async def dispatch_video(body: VideoReq):
    return await _dispatch_to_committee("video", body.model_dump())

app.include_router(router)
