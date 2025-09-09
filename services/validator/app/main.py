from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
import numpy as np

app = FastAPI(title="PrivacyX Validator")
router = APIRouter()

class AssessReq(BaseModel):
    probs: list[float]
    latencies_ms: list[int]
    z_threshold: float = 2.0
    trim_ratio: float = 0.2

def _trimmed_mean(vals, r):
    vals = sorted(vals)
    n, k = len(vals), int(len(vals)*r)
    vals = vals[k:n-k] if n>2*k else vals
    return float(np.mean(vals)) if len(vals) else 0.5

@router.post("/assess")
def assess(body: AssessReq):
    arr = np.array(body.probs, dtype=float)
    mu, sigma = float(np.mean(arr)), float(np.std(arr)+1e-9)
    z = np.abs((arr - mu)/sigma)
    inliers = arr[z <= body.z_threshold]
    outliers = arr[z > body.z_threshold]
    consensus = _trimmed_mean(inliers.tolist(), body.trim_ratio) if len(inliers) else _trimmed_mean(arr.tolist(), body.trim_ratio)
    std = float(np.std(inliers)) if len(inliers) else float(np.std(arr))
    confidence = max(0.0, min(1.0, 1.0 - std)) * (len(inliers)/max(1,len(arr)))
    return {
        "consensus_prob": round(consensus,4),
        "confidence": round(confidence,4),
        "inliers": int(len(inliers)),
        "outliers": int(len(outliers)),
        "flags": []
    }

app.include_router(router)
