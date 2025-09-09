from fastapi import FastAPI
from pydantic import BaseModel
from .infer import infer_image_prob, infer_video_prob
from .health import healthz

app = FastAPI(title="PrivacyX Miner")

class InferReq(BaseModel):
    type: str
    payload_b64: str | None = None
    source_url: str | None = None
    deadline_ms: int | None = 4000
    job_id: str | None = None

@app.get("/healthz")
def health():
    return healthz()

@app.post("/infer")
def infer(req: InferReq):
    if req.type == "image":
        return infer_image_prob(req)
    elif req.type == "video":
        return infer_video_prob(req)
    return {"prob":0.5,"uncertainty":0.5,"inference_ms":0,"model_id":"px-detector-v1"}
