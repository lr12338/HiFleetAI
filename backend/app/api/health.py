from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def read_health() -> dict[str, str]:
    return {
        "service": "HiFleetAI",
        "status": "ok",
        "api_version": "v1",
    }
