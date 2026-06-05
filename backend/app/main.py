from __future__ import annotations

from functools import lru_cache
import uuid

from fastapi import FastAPI, Request

from backend.app.api import api_router
from backend.app.core.config import Settings, get_settings


@lru_cache
def get_app_settings() -> Settings:
    return get_settings()


def create_app() -> FastAPI:
    settings = get_app_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.2.0-agent-api",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    app.include_router(api_router)
    return app


app = create_app()
