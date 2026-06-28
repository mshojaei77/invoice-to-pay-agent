from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(title="Invoice-to-Pay Agent")
app.include_router(router)
