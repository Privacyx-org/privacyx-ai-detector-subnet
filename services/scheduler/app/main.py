from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import os, itertools, httpx, asyncio, time, random
from typing import List, Dict

app = FastAPI()

MINER_URLS = [u.strip() for u in os.getenv("MINER_URLS", "http://127.0.0.1:6061").split(",") if u.strip()]
if not MINER_URLS:
    raise RuntimeError("No MINER_URLS provided")

# État des miners (santé, métriques simples)
_miners: List[Dict] = [{
    "url": u,
    "healthy": True,
    "fail_count": 0,
    "last_ok": 0.0,
} for u in MINER_URLS]

# Round-robin séparé pour les healthy
def _healthy_cycle():
    while True:
        healthy = [m for m in _miners if m["healthy"]]
        pool = healthy if healthy else _miners[:]  # fallback sur tous si aucun healthy
        for m in pool:
            yield m

_rr = _healthy_cycle()

@app.on_event("startup")
async def _start():
    # boucle de health-check en tâche de fond
    asyncio.create_task(_health_loop())

async def _health_loop():
    # ping régulier des miners, baisse/relève le flag healthy
    while True:
        await asyncio.gather(*[ _check_one(m) for m in _miners ])
        await asyncio.sleep(10)

async def _check_one(m: Dict):
    url = f'{m["url"]}/health'
    try:
        async with httpx.AsyncClient(timeout=5.0) as cx:
            r = await cx.get(url)
            m["healthy"] = (r.status_code == 200)
            if m["healthy"]:
                m["fail_count"] = 0
                m["last_ok"] = time.time()
    except Exception:
        m["healthy"] = False

@app.get("/health")
def health():
    return {
        "status": "ok",
        "miners": [m["url"] for m in _miners],
        "status_by_miner": [
            {"url": m["url"], "healthy": m["healthy"], "fail_count": m["fail_count"], "last_ok": m["last_ok"]}
            for m in _miners
        ],
    }

class ImageReq(BaseModel):
    source_url: HttpUrl | None = None
    image_b64: str | None = None

class VideoReq(BaseModel):
    video_url: HttpUrl

async def _forward_json(path: str, payload: dict):
    # retry avec backoff doux
    errors = []
    for attempt in range(3):
        target = next(_rr)
        url = f'{target["url"]}{path}'
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as cx:
                r = await cx.post(url, json=payload)
                if r.status_code >= 400:
                    raise HTTPException(r.status_code, f'miner error: {r.text}')
                data = r.json()
                data["miner_url"] = target["url"]
                # succès → on marque healthy
                target["healthy"] = True
                target["fail_count"] = 0
                target["last_ok"] = time.time()
                return data
        except HTTPException as e:
            target["fail_count"] += 1
            target["healthy"] = False
            errors.append((url, f'HTTP {e.status_code}'))
        except Exception as e:
            target["fail_count"] += 1
            target["healthy"] = False
            errors.append((url, str(e)))
        await asyncio.sleep(0.2 * (attempt + 1) + random.random() * 0.1)

    # si on est ici, 3 tentatives ont échoué
    detail = "; ".join([f"{u}: {msg}" for u, msg in errors])
    raise HTTPException(502, f"All miners failed: {detail}")

@app.post("/dispatch/image")
async def dispatch_image(req: ImageReq):
    if not (req.image_b64 or req.source_url):
        raise HTTPException(400, "image_b64 or source_url required")
    return await _forward_json("/infer/image", req.model_dump(mode="json"))

@app.post("/dispatch/video")
async def dispatch_video(req: VideoReq):
    return await _forward_json("/infer/video", req.model_dump(mode="json"))
