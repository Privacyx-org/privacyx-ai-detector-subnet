from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import os, itertools, httpx

app = FastAPI()

MINER_URLS = [u.strip() for u in os.getenv("MINER_URLS", "http://127.0.0.1:6061").split(",") if u.strip()]
if not MINER_URLS:
    raise RuntimeError("No MINER_URLS provided")

_rr = itertools.cycle(MINER_URLS)

@app.get("/health")
def health():
    return {"status": "ok", "miners": MINER_URLS}

class ImageReq(BaseModel):
    source_url: HttpUrl | None = None
    image_b64: str | None = None

class VideoReq(BaseModel):
    video_url: HttpUrl

async def _forward_json(path: str, payload: dict):
    target = next(_rr)
    url = f"{target}{path}"
    timeout = httpx.Timeout(20.0)
    async with httpx.AsyncClient(timeout=timeout) as cx:
        r = await cx.post(url, json=payload)
        if r.status_code >= 400:
            raise HTTPException(r.status_code, f"miner error: {r.text}")
        data = r.json()
        data["miner_url"] = target
        return data

@app.post("/dispatch/image")
async def dispatch_image(req: ImageReq):
    if not (req.image_b64 or req.source_url):
        raise HTTPException(400, "image_b64 or source_url required")
    return await _forward_json("/infer/image", req.model_dump(mode="json"))

@app.post("/dispatch/video")
async def dispatch_video(req: VideoReq):
    return await _forward_json("/infer/video", req.model_dump(mode="json"))
