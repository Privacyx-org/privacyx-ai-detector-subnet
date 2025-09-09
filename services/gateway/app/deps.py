import os
from fastapi import HTTPException
API_KEYS = set([k.strip() for k in os.getenv("API_KEYS","dev_key_123").split(",") if k.strip()])
def require_api_key(key: str | None):
    if (not key) or (key not in API_KEYS):
        raise HTTPException(401, "invalid api key")
