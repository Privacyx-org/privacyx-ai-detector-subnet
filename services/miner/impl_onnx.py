# services/miner/impl_onnx.py
import base64
import io
import os
from typing import Dict, Any, List, Tuple

import numpy as np
from PIL import Image

import onnxruntime as ort

IMAGENET_LABELS_PATH = os.getenv(
    "IMAGENET_LABELS_PATH",
    "/app/services/miner/models/imagenet_classes.txt",
)

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    "/app/services/miner/models/detector.onnx",
)

# Prétraitement ImageNet standard (224x224, RGB, NCHW, normalisation)
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def _load_labels(path: str) -> List[str]:
    labels = []
    with open(path, "r") as f:
        for line in f:
            labels.append(line.strip())
    # tolère les fichiers avec "index class" → garde juste la classe
    if labels and labels[0].split() and labels[0].split()[0].isdigit():
        labels = [" ".join(l.split()[1:]).strip() for l in labels]
    return labels


def _softmax(x: np.ndarray) -> np.ndarray:
    x = x - np.max(x, axis=-1, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=-1, keepdims=True)


def _preprocess_b64(image_b64: str) -> np.ndarray:
    # supporte data URL ou b64 pur
    if image_b64.startswith("data:"):
        image_b64 = image_b64.split(",", 1)[1]
    img_bytes = base64.b64decode(image_b64)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    # resize + center crop pour resnet50
    short_side = 256
    w, h = img.size
    if w < h:
        new_w = short_side
        new_h = int(h * short_side / w)
    else:
        new_h = short_side
        new_w = int(w * short_side / h)
    img = img.resize((new_w, new_h), Image.BILINEAR)

    # center crop 224x224
    left = (img.width - 224) // 2
    top = (img.height - 224) // 2
    img = img.crop((left, top, left + 224, top + 224))

    x = np.asarray(img).astype(np.float32) / 255.0
    x = (x - _MEAN) / _STD              # HWC, float32
    x = np.transpose(x, (2, 0, 1))      # -> CHW
    x = np.expand_dims(x, 0)            # -> NCHW
    return x


class OnnxDetector:
    def __init__(self) -> None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"MODEL_PATH not found: {MODEL_PATH}")
        self.labels = _load_labels(IMAGENET_LABELS_PATH)

        # Session ONNX
        sess_opts = ort.SessionOptions()
        # Optimisation niveau 3
        sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        # Threads via env (fallback 1)
        try:
            n_threads = int(os.getenv("ORT_NUM_THREADS", "1"))
        except ValueError:
            n_threads = 1
        sess_opts.intra_op_num_threads = max(1, n_threads)
        sess_opts.inter_op_num_threads = 1

        # Providers : CPU par défaut (explicite)
        providers = ["CPUExecutionProvider"]

        self.session = ort.InferenceSession(
            MODEL_PATH,
            sess_options=sess_opts,
            providers=providers,
        )

        # Entrée/sortie
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def _inference(self, x: np.ndarray) -> Tuple[int, float, np.ndarray]:
        outputs = self.session.run([self.output_name], {self.input_name: x})[0]
        # outputs shape -> (N, 1000) ou (1000,)
        logits = outputs[0] if outputs.ndim == 2 else outputs
        probs = _softmax(logits)
        top1_idx = int(np.argmax(probs))
        top1_prob = float(probs[top1_idx])
        return top1_idx, top1_prob, probs

    def detect_image(
        self,
        image_b64: str,
        return_explanation: bool = False
    ) -> Dict[str, Any]:
        x = _preprocess_b64(image_b64)
        idx, prob, probs = self._inference(x)

        label = self.labels[idx] if 0 <= idx < len(self.labels) else f"class_{idx}"

        result: Dict[str, Any] = {
            "detections": [
                {
                    "label": label,
                    "score": round(prob, 6),
                }
            ]
        }

        if return_explanation:
            # top-5
            top5_idx = np.argsort(-probs)[:5].tolist()
            top5 = []
            for i in top5_idx:
                lbl = self.labels[i] if 0 <= i < len(self.labels) else f"class_{i}"
                top5.append({"label": lbl, "score": float(round(probs[i], 6))})
            result["explanation"] = {"top5": top5}

        return result

