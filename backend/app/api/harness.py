from __future__ import annotations

from functools import lru_cache
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session, sessionmaker

from backend.app.auth.dependencies import get_current_principal
from backend.app.auth.service import AuthenticatedPrincipal
from backend.app.core.config import get_settings
from backend.app.db import create_session_factory
from backend.app.services.harness_service import (
    HarnessResultService,
    HarnessRunDetailRecord,
    HarnessRunNotFoundError,
    HarnessRunResultRecord,
    HarnessRunSummaryRecord,
)

router = APIRouter(prefix="/harness/runs", tags=["harness"])


@lru_cache
def get_harness_session_factory() -> sessionmaker[Session]:
    settings = get_settings()
    return create_session_factory(settings.database_url)


def get_harness_result_service() -> HarnessResultService:
    settings = get_settings()
    return HarnessResultService(
        session_factory=get_harness_session_factory(),
        report_dir=settings.harness_report_dir,
    )


class HarnessRunSummaryResponse(BaseModel):
    id: str
    source: str
    run_name: str | None
    status: str
    summary: dict | None
    created_at: datetime
    finished_at: datetime | None
    category: str | None = None
    agent_base_url: str | None = None


class HarnessRunListResponse(BaseModel):
    items: list[HarnessRunSummaryResponse]
    total: int


class HarnessRunResultResponse(BaseModel):
    id: str | None
    case_id: str | None
    status: str | None
    passed: bool | None
    score: float | None
    failure_reason: str | None
    actual_output: dict | None
    category: str | None = None
    assertions: list[dict] | None = None
    agent_result: dict | None
    created_at: datetime | None


class HarnessRunDetailResponse(HarnessRunSummaryResponse):
    model_configuration: dict | None = Field(alias="model_config")
    results: list[HarnessRunResultResponse]

    model_config = ConfigDict(populate_by_name=True)


@router.get("", response_model=HarnessRunListResponse)
def list_harness_runs(
    _: AuthenticatedPrincipal = Depends(get_current_principal),
    harness_service: HarnessResultService = Depends(get_harness_result_service),
) -> HarnessRunListResponse:
    runs = harness_service.list_runs()
    return HarnessRunListResponse(
        items=[_build_summary_response(run) for run in runs],
        total=len(runs),
    )


@router.get("/{run_id}", response_model=HarnessRunDetailResponse)
def get_harness_run_detail(
    run_id: str = Path(...),
    _: AuthenticatedPrincipal = Depends(get_current_principal),
    harness_service: HarnessResultService = Depends(get_harness_result_service),
) -> HarnessRunDetailResponse:
    try:
        run = harness_service.get_run(run_id=run_id)
    except HarnessRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _build_detail_response(run)


def _build_summary_response(run: HarnessRunSummaryRecord) -> HarnessRunSummaryResponse:
    return HarnessRunSummaryResponse(
        id=run.id,
        source=run.source,
        run_name=run.run_name,
        status=run.status,
        summary=run.summary,
        created_at=run.created_at,
        finished_at=run.finished_at,
        category=run.category,
        agent_base_url=run.agent_base_url,
    )


def _build_detail_response(run: HarnessRunDetailRecord) -> HarnessRunDetailResponse:
    return HarnessRunDetailResponse(
        id=run.id,
        source=run.source,
        run_name=run.run_name,
        status=run.status,
        summary=run.summary,
        created_at=run.created_at,
        finished_at=run.finished_at,
        category=run.category,
        agent_base_url=run.agent_base_url,
        model_configuration=run.model_config,
        results=[_build_result_response(result) for result in run.results],
    )


def _build_result_response(result: HarnessRunResultRecord) -> HarnessRunResultResponse:
    return HarnessRunResultResponse(
        id=result.id,
        case_id=result.case_id,
        status=result.status,
        passed=result.passed,
        score=result.score,
        failure_reason=result.failure_reason,
        actual_output=result.actual_output,
        category=result.category,
        assertions=result.assertions,
        agent_result=result.agent_result,
        created_at=result.created_at,
    )
