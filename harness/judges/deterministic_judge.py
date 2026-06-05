"""Deterministic assertions for Harness results.

This judge intentionally checks only structured fields. It does not call an LLM
and it does not infer success when the Agent API is unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


REQUIRED_SUCCESS_FIELDS = (
    "conversation_id",
    "message_id",
    "reply",
    "handoff_status",
    "tool_calls",
    "sources",
)


@dataclass(frozen=True)
class AssertionResult:
    name: str
    passed: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "passed": self.passed, "message": self.message}


def judge_case(case: dict[str, Any], agent_result: dict[str, Any]) -> dict[str, Any]:
    """Judge one case using deterministic structure checks."""
    assertions: list[AssertionResult] = []
    status = agent_result.get("status")

    if status != "success":
        failure_reason = _failure_reason(agent_result)
        assertions.append(
            AssertionResult(
                name="agent_status",
                passed=False,
                message=f"Agent result status is {status!r}; {failure_reason}",
            )
        )
        return _result(case, agent_result, assertions, failure_reason)

    response = agent_result.get("response")
    response_is_object = isinstance(response, dict)
    assertions.append(
        AssertionResult(
            name="response_object",
            passed=response_is_object,
            message="Response must be a JSON object.",
        )
    )

    if not response_is_object:
        return _result(case, agent_result, assertions, "Agent response is not a JSON object.")

    for field_name in REQUIRED_SUCCESS_FIELDS:
        assertions.append(
            AssertionResult(
                name=f"field:{field_name}",
                passed=field_name in response,
                message=f"Response must include {field_name}.",
            )
        )

    reply = response.get("reply")
    assertions.append(
        AssertionResult(
            name="reply_shape",
            passed=isinstance(reply, dict) and isinstance(reply.get("content"), str),
            message="Response reply must include text content.",
        )
    )

    expected_handoff = case.get("expect", {}).get("expected_handoff_status")
    if expected_handoff is not None:
        assertions.append(
            AssertionResult(
                name="handoff_status",
                passed=response.get("handoff_status") == expected_handoff,
                message=f"Handoff status must be {expected_handoff}.",
            )
        )

    expected_sequence = case.get("expect", {}).get("expected_sequence")
    if isinstance(expected_sequence, list):
        actual_sequence = response.get("sequence")
        assertions.append(
            AssertionResult(
                name="handoff_sequence_shape",
                passed=isinstance(actual_sequence, list),
                message="Handoff response must include a sequence list.",
            )
        )
        if isinstance(actual_sequence, list):
            assertions.append(
                AssertionResult(
                    name="handoff_sequence_length",
                    passed=len(actual_sequence) == len(expected_sequence),
                    message=f"Handoff sequence must contain {len(expected_sequence)} steps.",
                )
            )
            for index, expected_step in enumerate(expected_sequence):
                if index >= len(actual_sequence):
                    break
                actual_step = actual_sequence[index]
                assertions.append(
                    AssertionResult(
                        name=f"handoff_step_{index}_action",
                        passed=actual_step.get("action") == expected_step.get("action"),
                        message=f"Handoff step {index} action must be {expected_step.get('action')}.",
                    )
                )
                assertions.append(
                    AssertionResult(
                        name=f"handoff_step_{index}_http_status",
                        passed=actual_step.get("http_status") == expected_step.get("http_status"),
                        message=f"Handoff step {index} HTTP status must be {expected_step.get('http_status')}.",
                    )
                )
                assertions.append(
                    AssertionResult(
                        name=f"handoff_step_{index}_status",
                        passed=actual_step.get("handoff_status") == expected_step.get("handoff_status"),
                        message=(
                            f"Handoff step {index} status must be "
                            f"{expected_step.get('handoff_status')}."
                        ),
                    )
                )

    failure_reason = _first_failure(assertions)
    return _result(case, agent_result, assertions, failure_reason)


def _result(
    case: dict[str, Any],
    agent_result: dict[str, Any],
    assertions: list[AssertionResult],
    failure_reason: str | None,
) -> dict[str, Any]:
    passed = failure_reason is None
    return {
        "case_id": case["id"],
        "category": case["category"],
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "status": "passed" if passed else "failed",
        "failure_reason": failure_reason,
        "assertions": [assertion.to_dict() for assertion in assertions],
        "agent_result": agent_result,
    }


def _failure_reason(agent_result: dict[str, Any]) -> str:
    reason = agent_result.get("failure_reason")
    if isinstance(reason, str) and reason:
        return reason
    return "Agent API returned a non-success status."


def _first_failure(assertions: list[AssertionResult]) -> str | None:
    for assertion in assertions:
        if not assertion.passed:
            return assertion.message
    return None
