from __future__ import annotations

import json
from pathlib import Path

from harness.runners import run_eval


def test_load_cases_includes_initial_categories() -> None:
    cases = run_eval.load_cases()
    categories = {case["category"] for case in cases}

    assert {"faq", "rag", "skill", "handoff", "regression"}.issubset(categories)
    assert all(case["id"] for case in cases)


def test_list_cases_prints_loaded_cases(capsys) -> None:
    exit_code = run_eval.main(["--list-cases"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "faq_001\tfaq" in output
    assert "rag_001\trag" in output
    assert "skill_001\tskill" in output
    assert "handoff_001\thandoff" in output
    assert "regression_001\tregression" in output


def test_unavailable_agent_api_writes_structured_failure_report(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def unavailable_client(case, agent_base_url):
        return {
            "status": "service_unavailable",
            "http_status": None,
            "latency_ms": 1,
            "response": None,
            "failure_reason": "Agent API unavailable: service unavailable",
        }

    monkeypatch.setenv("HARNESS_REPORT_DIR", str(tmp_path))
    monkeypatch.setenv("HARNESS_AGENT_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setattr(run_eval, "call_agent_api", unavailable_client)

    exit_code = run_eval.main(["--category", "faq"])

    latest_json = tmp_path / "latest.json"
    latest_md = tmp_path / "latest.md"
    report = json.loads(latest_json.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert latest_json.exists()
    assert latest_md.exists()
    assert report["status"] == "failed"
    assert report["summary"] == {"total": 1, "passed": 0, "failed": 1, "pass_rate": 0.0}
    assert report["results"][0]["case_id"] == "faq_001"
    assert report["results"][0]["passed"] is False
    assert report["results"][0]["failure_reason"] == "Agent API unavailable: service unavailable"
    assert "Agent API unavailable: service unavailable" in latest_md.read_text(encoding="utf-8")
