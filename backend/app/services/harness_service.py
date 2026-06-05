from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.models import HarnessResult, HarnessRun

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class HarnessRunNotFoundError(ValueError):
    """Raised when a requested harness run cannot be found."""


@dataclass(frozen=True)
class HarnessRunSummaryRecord:
    id: str
    source: str
    run_name: str | None
    status: str
    summary: dict[str, Any] | None
    created_at: datetime
    finished_at: datetime | None
    category: str | None = None
    agent_base_url: str | None = None


@dataclass(frozen=True)
class HarnessRunResultRecord:
    id: str | None
    case_id: str | None
    status: str | None
    passed: bool | None
    score: float | None
    failure_reason: str | None
    actual_output: dict[str, Any] | None
    category: str | None
    assertions: list[dict[str, Any]] | None
    agent_result: dict[str, Any] | None
    created_at: datetime | None


@dataclass(frozen=True)
class HarnessRunDetailRecord(HarnessRunSummaryRecord):
    model_config: dict[str, Any] | None = None
    results: list[HarnessRunResultRecord] = field(default_factory=list)


class HarnessResultService:
    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        report_dir: str | Path,
    ) -> None:
        self._session_factory = session_factory
        self._report_dir = self._resolve_report_dir(report_dir)

    def list_runs(self) -> list[HarnessRunSummaryRecord]:
        runs_by_id: dict[str, HarnessRunSummaryRecord] = {}

        with self._session_factory() as session:
            statement = select(HarnessRun).order_by(HarnessRun.created_at.desc(), HarnessRun.id.desc())
            for run in session.scalars(statement).all():
                summary = self._build_db_summary(run)
                runs_by_id[summary.id] = summary

        latest_report = self._load_latest_report()
        if latest_report is not None and latest_report.id not in runs_by_id:
            runs_by_id[latest_report.id] = latest_report

        return sorted(runs_by_id.values(), key=lambda item: (item.created_at, item.id), reverse=True)

    def get_run(self, *, run_id: str) -> HarnessRunDetailRecord:
        with self._session_factory() as session:
            run = session.get(HarnessRun, run_id)
            if run is not None:
                result_statement = (
                    select(HarnessResult)
                    .where(HarnessResult.run_id == run_id)
                    .order_by(HarnessResult.created_at.asc(), HarnessResult.id.asc())
                )
                results = [
                    self._build_db_result(result)
                    for result in session.scalars(result_statement).all()
                ]
                summary = self._build_db_summary(run)
                return HarnessRunDetailRecord(
                    id=summary.id,
                    source=summary.source,
                    run_name=summary.run_name,
                    status=summary.status,
                    summary=summary.summary,
                    created_at=summary.created_at,
                    finished_at=summary.finished_at,
                    category=summary.category,
                    agent_base_url=summary.agent_base_url,
                    model_config=self._normalize_dict(run.model_config),
                    results=results,
                )

        latest_report = self._load_latest_report()
        if latest_report is not None and latest_report.id == run_id:
            return self._build_file_detail(run_id=run_id)

        raise HarnessRunNotFoundError(f"Harness run '{run_id}' was not found")

    def _load_latest_report(self) -> HarnessRunSummaryRecord | None:
        report_path = self._report_dir / "latest.json"
        if not report_path.exists():
            return None

        payload = json.loads(report_path.read_text(encoding="utf-8"))
        return self._build_file_summary(payload)

    def _build_file_detail(self, *, run_id: str) -> HarnessRunDetailRecord:
        report_path = self._report_dir / "latest.json"
        if not report_path.exists():
            raise HarnessRunNotFoundError(f"Harness run '{run_id}' was not found")

        payload = json.loads(report_path.read_text(encoding="utf-8"))
        if payload.get("run_id") != run_id:
            raise HarnessRunNotFoundError(f"Harness run '{run_id}' was not found")

        summary = self._build_file_summary(payload)
        results = [
            HarnessRunResultRecord(
                id=None,
                case_id=result.get("case_id"),
                status=result.get("status"),
                passed=result.get("passed"),
                score=self._normalize_score(result.get("score")),
                failure_reason=result.get("failure_reason"),
                actual_output=None,
                category=result.get("category"),
                assertions=self._normalize_assertions(result.get("assertions")),
                agent_result=self._normalize_dict(result.get("agent_result")),
                created_at=None,
            )
            for result in payload.get("results", [])
        ]
        return HarnessRunDetailRecord(
            id=summary.id,
            source=summary.source,
            run_name=summary.run_name,
            status=summary.status,
            summary=summary.summary,
            created_at=summary.created_at,
            finished_at=summary.finished_at,
            category=summary.category,
            agent_base_url=summary.agent_base_url,
            model_config=None,
            results=results,
        )

    @staticmethod
    def _build_db_summary(run: HarnessRun) -> HarnessRunSummaryRecord:
        return HarnessRunSummaryRecord(
            id=run.id,
            source="database",
            run_name=run.run_name,
            status=run.status,
            summary=HarnessResultService._normalize_dict(run.summary),
            created_at=HarnessResultService._normalize_datetime(run.created_at),
            finished_at=HarnessResultService._normalize_datetime(run.finished_at),
        )

    @staticmethod
    def _build_db_result(result: HarnessResult) -> HarnessRunResultRecord:
        return HarnessRunResultRecord(
            id=result.id,
            case_id=result.case_id,
            status=HarnessResultService._derive_result_status(result.passed),
            passed=result.passed,
            score=HarnessResultService._normalize_score(result.score),
            failure_reason=result.failure_reason,
            actual_output=HarnessResultService._normalize_dict(result.actual_output),
            category=None,
            assertions=None,
            agent_result=None,
            created_at=HarnessResultService._normalize_datetime(result.created_at),
        )

    @staticmethod
    def _build_file_summary(payload: dict[str, Any]) -> HarnessRunSummaryRecord:
        return HarnessRunSummaryRecord(
            id=str(payload["run_id"]),
            source="report_file",
            run_name=str(payload["run_id"]),
            status=str(payload["status"]),
            summary=HarnessResultService._normalize_dict(payload.get("summary")),
            created_at=HarnessResultService._parse_datetime(payload.get("started_at")),
            finished_at=HarnessResultService._parse_datetime(payload.get("finished_at")),
            category=payload.get("category"),
            agent_base_url=payload.get("agent_base_url"),
        )

    @staticmethod
    def _resolve_report_dir(report_dir: str | Path) -> Path:
        resolved = Path(report_dir)
        if resolved.is_absolute():
            return resolved
        return PROJECT_ROOT / resolved

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        if not isinstance(value, str) or not value:
            raise ValueError("Harness report is missing a valid datetime field")
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed
        return parsed.astimezone(UTC).replace(tzinfo=None)

    @staticmethod
    def _normalize_datetime(value: object | None) -> datetime | None:
        if not isinstance(value, datetime):
            return None
        if value.tzinfo is None:
            return value
        return value.astimezone(UTC).replace(tzinfo=None)

    @staticmethod
    def _normalize_score(value: Any) -> float | None:
        if value is None:
            return None
        return float(value)

    @staticmethod
    def _derive_result_status(passed: bool | None) -> str | None:
        if passed is None:
            return None
        return "passed" if passed else "failed"

    @staticmethod
    def _normalize_dict(value: Any) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            return None
        return dict(value)

    @staticmethod
    def _normalize_assertions(value: Any) -> list[dict[str, Any]] | None:
        if not isinstance(value, list):
            return None
        assertions: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, dict):
                assertions.append(dict(item))
        return assertions
