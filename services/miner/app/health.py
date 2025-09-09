import os
def healthz():
  return {"model_id": os.getenv("MODEL_ID","px-detector-v1"), "model_hash":"sha256:unknown", "queue":0}
