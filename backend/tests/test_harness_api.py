from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import Base, create_engine_for_url
from backend.app.main import create_app
from backend.app.models import HarnessResult, HarnessRun
from backend.app.services.harness_service import HarnessResultService


def build_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine_for_url(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def build_client(tmp_path: Path):
    from backend.app.api.harness import get_harness_result_service
    from backend.app.auth.dependencies import get_auth_service
    from backend.app.auth.service import AuthService

    database_url = f"sqlite:///{tmp_path / 'harness-api-test.db'}"
    session_factory = build_session_factory(database_url)
    auth_service = AuthService(
        session_factory=session_factory,
        jwt_secret="unit-test-secret-key-with-32-bytes",
        access_token_expire_minutes=15,
    )
    auth_service.create_local_user(
        username="admin_user",
        password="correct-password",
        display_name="Admin User",
        role="admin",
    )

    report_dir = tmp_path / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    harness_service = HarnessResultService(
        session_factory=session_factory,
        report_dir=report_dir,
    )

    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_harness_result_service] = lambda: harness_service
    client = TestClient(app)
    return client, auth_service, session_factory, report_dir


def login(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin_user",
            "password": "correct-password",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def seed_database_run(session_factory: sessionmaker[Session]) -> str:
    started_at = datetime(2026, 6, 3, 15, 0, tzinfo=UTC)
    finished_at = datetime(2026, 6, 3, 15, 5, tzinfo=UTC)
    first_case_id = str(uuid.uuid4())
    second_case_id = str(uuid.uuid4())

    with session_factory() as session:
        run = HarnessRun(
            run_name="Regression smoke",
            status="failed",
            model_config={"provider": "ark", "model": "deepseek-v4-flash-260425"},
            summary={"total": 2, "passed": 1, "failed": 1, "pass_rate": 0.5},
            created_at=started_at,
            finished_at=finished_at,
        )
        session.add(run)
        session.flush()
        session.add_all(
            [
                HarnessResult(
                    run_id=run.id,
                    case_id=first_case_id,
                    actual_output={"reply": {"type": "text", "content": "正常返回"}},
                    score=1.0,
                    passed=True,
                    failure_reason=None,
                    created_at=started_at,
                ),
                HarnessResult(
                    run_id=run.id,
                    case_id=second_case_id,
                    actual_output={"reply": {"type": "text", "content": "缺少关键信息"}},
                    score=0.0,
                    passed=False,
                    failure_reason="Expected refund policy reference.",
                    created_at=finished_at,
                ),
            ]
        )
        session.commit()
        return run.id


def write_report(report_dir: Path) -> str:
    payload = {
        "run_id": "run_20260603_160000",
        "started_at": "2026-06-03T16:00:00+00:00",
        "finished_at": "2026-06-03T16:00:03+00:00",
        "category": "handoff",
        "agent_base_url": "http://localhost:8000",
        "status": "passed",
        "summary": {"total": 1, "passed": 1, "failed": 0, "pass_rate": 1.0},
        "results": [
            {
                "case_id": "handoff_001",
                "category": "handoff",
                "passed": True,
                "score": 1.0,
                "status": "passed",
                "failure_reason": None,
                "assertions": [{"name": "handoff_status", "passed": True, "message": "ok"}],
                "agent_result": {
                    "status": "success",
                    "http_status": 200,
                    "latency_ms": 42,
                    "response": {"handoff_status": "ai_active"},
                    "failure_reason": None,
                },
            }
        ],
    }
    (report_dir / "latest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload["run_id"]


def test_harness_run_list_requires_login(tmp_path: Path) -> None:
    client, _, _, _ = build_client(tmp_path)

    response = client.get("/api/v1/harness/runs")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_harness_run_list_returns_report_summary_when_database_empty(tmp_path: Path) -> None:
    client, _, _, report_dir = build_client(tmp_path)
    report_run_id = write_report(report_dir)
    access_token = login(client)

    response = client.get(
        "/api/v1/harness/runs",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"] == [
        {
            "id": report_run_id,
            "source": "report_file",
            "run_name": report_run_id,
            "status": "passed",
            "summary": {"total": 1, "passed": 1, "failed": 0, "pass_rate": 1.0},
            "created_at": "2026-06-03T16:00:00",
            "finished_at": "2026-06-03T16:00:03",
            "category": "handoff",
            "agent_base_url": "http://localhost:8000",
        }
    ]


def test_harness_run_detail_returns_database_results(tmp_path: Path) -> None:
    client, _, session_factory, _ = build_client(tmp_path)
    run_id = seed_database_run(session_factory)
    access_token = login(client)

    response = client.get(
        f"/api/v1/harness/runs/{run_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == run_id
    assert payload["source"] == "database"
    assert payload["run_name"] == "Regression smoke"
    assert payload["status"] == "failed"
    assert payload["summary"] == {"total": 2, "passed": 1, "failed": 1, "pass_rate": 0.5}
    assert payload["model_config"] == {"provider": "ark", "model": "deepseek-v4-flash-260425"}
    assert len(payload["results"]) == 2
    assert all(result["case_id"] for result in payload["results"])
    assert payload["results"][0]["passed"] is True
    assert payload["results"][0]["status"] == "passed"
    assert payload["results"][0]["actual_output"] == {"reply": {"type": "text", "content": "正常返回"}}
    assert payload["results"][1]["passed"] is False
    assert payload["results"][1]["status"] == "failed"
    assert payload["results"][1]["failure_reason"] == "Expected refund policy reference."


def test_harness_run_list_returns_empty_when_no_database_or_report_data(tmp_path: Path) -> None:
    client, _, _, _ = build_client(tmp_path)
    access_token = login(client)

    response = client.get(
        "/api/v1/harness/runs",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


def test_harness_run_detail_returns_404_for_missing_run(tmp_path: Path) -> None:
    client, _, _, _ = build_client(tmp_path)
    access_token = login(client)

    response = client.get(
        "/api/v1/harness/runs/run_missing",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Harness run 'run_missing' was not found"}
