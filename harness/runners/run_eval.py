"""Executable Harness runner for Phase 0 skeleton evaluations."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Callable
from urllib import error, request


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from harness.judges.deterministic_judge import judge_case  # noqa: E402


CASE_DIR = PROJECT_ROOT / "harness" / "cases"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "harness" / "reports"
DEFAULT_AGENT_BASE_URL = "http://localhost:8000"
CHAT_PATH = "/api/v1/chat"

AgentClient = Callable[[dict[str, Any], str], dict[str, Any]]


def load_cases(case_dir: Path = CASE_DIR, category: str | None = None) -> list[dict[str, Any]]:
    """Load and validate JSONL cases, optionally filtered by category."""
    cases: list[dict[str, Any]] = []
    for case_file in sorted(case_dir.glob("*_cases.jsonl")):
        with case_file.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, 1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    case = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON in {case_file}:{line_number}: {exc}") from exc
                _validate_case(case, case_file, line_number)
                if category is None or case["category"] == category:
                    cases.append(case)
    return sorted(cases, key=lambda item: item["id"])


def run_cases(
    cases: list[dict[str, Any]],
    *,
    category: str,
    agent_base_url: str,
    agent_client: AgentClient | None = None,
) -> dict[str, Any]:
    """Run cases and return a structured report payload."""
    started_at = _timestamp()
    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    client = agent_client or call_agent_api
    results = []

    for case in cases:
        agent_result = client(case, agent_base_url)
        results.append(judge_case(case, agent_result))

    finished_at = _timestamp()
    passed = sum(1 for result in results if result["passed"])
    failed = len(results) - passed
    pass_rate = passed / len(results) if results else 0.0
    run_status = "passed" if failed == 0 and results else "failed"
    if not results:
        run_status = "no_cases"

    return {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "category": category,
        "agent_base_url": agent_base_url,
        "status": run_status,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
        },
        "results": results,
    }


def call_agent_api(case: dict[str, Any], agent_base_url: str) -> dict[str, Any]:
    """Call the Agent API using the standard library and return a structured result."""
    url = agent_base_url.rstrip("/") + CHAT_PATH
    payload = {
        "conversation_id": None,
        "channel_type": case["input"]["channel_type"],
        "user": {"user_id": None, "display_name": "Harness Test User"},
        "message": {
            "type": case["input"]["message_type"],
            "content": case["input"]["content"],
            "attachments": case["input"].get("attachments", []),
        },
        "metadata": {"source": "harness", "case_id": case["id"]},
    }
    started = time.perf_counter()
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    http_request = request.Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=3) as response:
            body = response.read().decode("utf-8")
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            response_payload = json.loads(body) if body else {}
            return {
                "status": "success",
                "http_status": response.status,
                "latency_ms": elapsed_ms,
                "response": response_payload,
                "failure_reason": None,
            }
    except error.HTTPError as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return _unavailable_result(f"Agent API unavailable: HTTP {exc.code}", elapsed_ms)
    except (error.URLError, TimeoutError, OSError) as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return _unavailable_result(f"Agent API unavailable: {exc}", elapsed_ms)
    except json.JSONDecodeError as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {
            "status": "invalid_response",
            "http_status": 200,
            "latency_ms": elapsed_ms,
            "response": None,
            "failure_reason": f"Agent API returned invalid JSON: {exc}",
        }


def write_reports(report: dict[str, Any], report_dir: Path) -> tuple[Path, Path]:
    """Write latest JSON and Markdown reports."""
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "latest.json"
    markdown_path = report_dir / "latest.md"

    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def print_case_list(cases: list[dict[str, Any]]) -> None:
    for case in cases:
        description = case.get("metadata", {}).get("description", "")
        print(f"{case['id']}\t{case['category']}\t{case['phase']}\t{description}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run HiFleetAI Harness evaluations.")
    parser.add_argument("--list-cases", action="store_true", help="List all loaded cases.")
    parser.add_argument("--category", help="Run only cases in one category.")
    args = parser.parse_args(argv)

    if args.list_cases:
        print_case_list(load_cases())
        return 0

    if not args.category:
        parser.error("--category is required unless --list-cases is used")

    cases = load_cases(category=args.category)
    report_dir = Path(os.environ.get("HARNESS_REPORT_DIR", str(DEFAULT_REPORT_DIR)))
    agent_base_url = os.environ.get("HARNESS_AGENT_BASE_URL", DEFAULT_AGENT_BASE_URL)
    report = run_cases(cases, category=args.category, agent_base_url=agent_base_url)
    json_path, markdown_path = write_reports(report, report_dir)
    print(
        "Harness run completed: "
        f"status={report['status']} total={report['summary']['total']} "
        f"passed={report['summary']['passed']} failed={report['summary']['failed']}"
    )
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    return 0


def _validate_case(case: dict[str, Any], case_file: Path, line_number: int) -> None:
    required_top_level = ("id", "category", "phase", "input", "expect", "metadata")
    for field_name in required_top_level:
        if field_name not in case:
            raise ValueError(f"Missing {field_name!r} in {case_file}:{line_number}")

    if not isinstance(case["id"], str) or not case["id"]:
        raise ValueError(f"Invalid case id in {case_file}:{line_number}")
    if not isinstance(case["category"], str) or not case["category"]:
        raise ValueError(f"Invalid category in {case_file}:{line_number}")
    if not isinstance(case["input"], dict):
        raise ValueError(f"Invalid input in {case_file}:{line_number}")
    if not isinstance(case["expect"], dict):
        raise ValueError(f"Invalid expect in {case_file}:{line_number}")

    for field_name in ("channel_type", "message_type", "content", "attachments"):
        if field_name not in case["input"]:
            raise ValueError(f"Missing input.{field_name} in {case_file}:{line_number}")
    if not isinstance(case["input"]["attachments"], list):
        raise ValueError(f"input.attachments must be a list in {case_file}:{line_number}")


def _unavailable_result(failure_reason: str, latency_ms: int) -> dict[str, Any]:
    return {
        "status": "service_unavailable",
        "http_status": None,
        "latency_ms": latency_ms,
        "response": None,
        "failure_reason": failure_reason,
    }


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    pass_rate = f"{summary['pass_rate']:.0%}"
    lines = [
        "# Harness Report",
        "",
        f"- Run ID: {report['run_id']}",
        f"- Status: {report['status']}",
        f"- Category: {report['category']}",
        f"- Agent Base URL: {report['agent_base_url']}",
        f"- Started At: {report['started_at']}",
        f"- Finished At: {report['finished_at']}",
        f"- Total: {summary['total']}",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        f"- Pass Rate: {pass_rate}",
        "",
        "## Failed Cases",
        "",
    ]

    failed_cases = [result for result in report["results"] if not result["passed"]]
    if not failed_cases:
        lines.append("No failed cases.")
    else:
        for result in failed_cases:
            lines.extend(
                [
                    f"### {result['case_id']}",
                    "",
                    f"- Category: {result['category']}",
                    f"- Reason: {result['failure_reason']}",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
