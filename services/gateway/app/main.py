from fastapi import FastAPI
from .api import router as api_router
app = FastAPI(title="PrivacyX Gateway")
app.include_router(api_router, prefix="/v1")
