from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import os, time

# --- Optional model deps
MODEL_IMPL = os.getenv("MODEL_IMPL", "stub").lower()  # "stub" | "onnx"
MODEL_PATH = os.getenv("MODEL_PATH", "services/miner/models/detector.onnx")

# lazy imports
_onnx_session = None
_np = None
_Image = None

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "model_impl": MODEL_IMPL, "model_path": MODEL_PATH if MODEL_IMPL=="onnx" else None}

class ImageReq(BaseModel):
    source_url: HttpUrl | None = None
    image_b64: str | None = None

class VideoReq(BaseModel):
    video_url: HttpUrl

# --- utils
def _load_from_data_url(data_url: str):
    # data:image/png;base64,XXXX...
    import base64, re, io
    m = re.match(r"^data:.*?;base64,(.*)$", data_url)
    if not m:
        raise ValueError("Invalid data URL")
    return base64.b64decode(m.group(1))

def _fetch_bytes(url: str) -> bytes:
    import httpx
    with httpx.Client(timeout=15.0) as cx:
        r = cx.get(url)
        r.raise_for_status()
        return r.content

def _ensure_onnx():
    global _onnx_session, _np, _Image
    if _onnx_session is not None:
        return
    import onnxruntime as ort
    import numpy as np
    from PIL import Image
    _np = np
    _Image = Image
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"MODEL_PATH not found: {MODEL_PATH}")
    providers = ["CPUExecutionProvider"]
    _onnx_session = ort.InferenceSession(MODEL_PATH, providers=providers)

def _preprocess_img(img_bytes: bytes, size: int = 224):
    # Image → NCHW float32 [0..1], mean/std ImageNet
    img = _Image.open(io:=__import__("io").BytesIO(img_bytes)).convert("RGB")
    img = img.resize((size, size))
    arr = _np.asarray(img).astype("float32") / 255.0
    mean = _np.array([0.485, 0.456, 0.406], dtype=_np.float32)
    std  = _np.array([0.229, 0.224, 0.225], dtype=_np.float32)
    arr = (arr - mean) / std
    arr = _np.transpose(arr, (2, 0, 1))  # HWC->CHW
    arr = _np.expand_dims(arr, 0)        # NCHW
    return arr

def _run_onnx(img_bytes: bytes):
    _ensure_onnx()
    inp = _preprocess_img(img_bytes)
    input_name = _onnx_session.get_inputs()[0].name
    out_names = [o.name for o in _onnx_session.get_outputs()]
    outputs = _onnx_session.run(out_names, {input_name: inp})
    # Simplissime: prend l’argmax du 1er tensor
    logits = outputs[0]
    cls = int(_np.argmax(logits))
    score = float(_np.max(logits)) if logits.ndim >= 2 else 0.0
    # NB: "cat" est fictif tant que tu n’as pas de mapping de classes
    return [{"label": f"class_{cls}", "score": round(score, 5)}]

@app.post("/infer/image")
def infer_image(req: ImageReq):
    if not (req.image_b64 or req.source_url):
        raise HTTPException(400, "image_b64 or source_url required")
    t0 = time.time()

    # Charge les bytes
    try:
        if req.image_b64:
            img_bytes = _load_from_data_url(req.image_b64)
        else:
            img_bytes = _fetch_bytes(str(req.source_url))
    except Exception as e:
        raise HTTPException(400, f"fetch/decode error: {e}")

    # Exécute le modèle (ou stub)
    try:
        if MODEL_IMPL == "onnx":
            dets = _run_onnx(img_bytes)
        else:
            dets = [{"label":"cat","score":0.88}]
    except Exception as e:
        # fallback de sécurité vers stub si onnx plante
        dets = [{"label":"cat","score":0.88, "note": f"onnx_error: {e}"}]

    return {"detections": dets, "label": "uncertain", "latency_ms": int((time.time()-t0)*1000)}

@app.post("/infer/video")
def infer_video(req: VideoReq):
    t0 = time.time()
    # TODO: échantillonnage de frames + inférence; pour l’instant stub
    dets = [{"label":"bunny","score":0.91}]
    return {"detections": dets, "label": "uncertain", "latency_ms": int((time.time()-t0)*1000)}
