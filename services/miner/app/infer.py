import os, time, base64
import numpy as np, cv2
from pydantic import BaseModel

MODEL_ID = os.getenv("MODEL_ID","px-detector-v1")
MODEL_PATH = os.getenv("MODEL_PATH","/app/models/detector.onnx")
MODEL_HASH = os.getenv("MODEL_HASH","sha256:unknown")
NODE_ID = os.getenv("NODE_ID","miner_local")
IMG_SIZE = int(os.getenv("IMG_SIZE","224"))
MEAN = np.array([0.485,0.456,0.406], dtype=np.float32)
STD  = np.array([0.229,0.224,0.225], dtype=np.float32)

ORT = None
if os.path.exists(MODEL_PATH):
    try:
        import onnxruntime as ort
        ORT = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
        IN_NAME = ORT.get_inputs()[0].name
        OUT_NAME = ORT.get_outputs()[0].name
    except Exception:
        ORT = None

class Req(BaseModel):
    type: str
    payload_b64: str | None = None
    source_url: str | None = None
    deadline_ms: int | None = 4000
    job_id: str | None = None

def _decode_image_b64(b64url: str) -> np.ndarray | None:
    try:
        if b64url.startswith("data:"):
            b64 = b64url.split(",",1)[1]
        else:
            b64 = b64url
        raw = base64.b64decode(b64)
        arr = np.frombuffer(raw, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None

def _preprocess_bchw(img_bgr: np.ndarray) -> np.ndarray:
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    img_rgb = cv2.resize(img_rgb, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)
    x = img_rgb.astype(np.float32)/255.0
    x = (x - MEAN) / STD
    x = np.transpose(x, (2,0,1))  # HWC->CHW
    x = np.expand_dims(x, 0)      # NCHW
    return x

def _postprocess(y: np.ndarray) -> float:
    if y.ndim == 2 and y.shape[1] == 1:
        prob = float(1/(1+np.exp(-y[0,0])))
    elif y.ndim == 2 and y.shape[1] == 2:
        e = np.exp(y - y.max())
        sm = e / e.sum(axis=1, keepdims=True)
        prob = float(sm[0,1])
    else:
        prob = float(y.ravel()[0])
    return max(0.0, min(1.0, prob))

def _heuristic(img: np.ndarray) -> float:
    if img is None:
        return 0.5
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    ratio = float((edges>0).sum()) / float(gray.size)
    return float(max(0.01, min(0.99, ratio*3)))

def infer_image_prob(req: Req):
    t0 = time.perf_counter()
    img = _decode_image_b64(req.payload_b64 or "")
    if img is None:
        return {"prob":0.5,"uncertainty":0.5,"inference_ms":0,"model_id":MODEL_ID,"model_hash":MODEL_HASH,"node_id":NODE_ID}
    if ORT is not None:
        x = _preprocess_bchw(img)
        y = ORT.run([OUT_NAME], {IN_NAME: x})[0]
        prob = _postprocess(y)
    else:
        prob = _heuristic(img)
    uncert = float(1.0 - min(1.0, abs(prob-0.5)*2))
    return {
        "prob": round(prob,4),
        "uncertainty": round(uncert,4),
        "inference_ms": int((time.perf_counter()-t0)*1000),
        "model_id": MODEL_ID,
        "model_hash": MODEL_HASH,
        "node_id": NODE_ID
    }

def infer_video_prob(req: Req):
    return infer_image_prob(req)
