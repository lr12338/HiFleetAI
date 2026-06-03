from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.auth import router as auth_router
from backend.app.api.health import router as health_router

api_router = APIRouter(prefix="/api")
v1_router = APIRouter(prefix="/v1")

api_router.include_router(health_router)
v1_router.include_router(auth_router)
api_router.include_router(v1_router)
