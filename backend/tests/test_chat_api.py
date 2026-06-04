from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app


def build_chat_payload(content: str) -> dict:
    return {
        "conversation_id": None,
        "channel_type": "console",
        "user": {"user_id": None, "display_name": "Harness Test User"},
        "message": {
            "type": "text",
            "content": content,
            "attachments": [],
        },
        "metadata": {"source": "pytest"},
    }


def test_chat_endpoint_returns_structured_failure_for_unavailable_model(monkeypatch) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "ark")
    monkeypatch.setenv("ARK_API_KEY", "")
    client = TestClient(app)

    response = client.post(
        "/api/v1/chat",
        json=build_chat_payload("如果模型或服务不可用，Hifleet 客服 Agent 应该如何响应？"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["conversation_id"], str)
    assert isinstance(payload["message_id"], str)
    assert payload["reply"]["type"] == "text"
    assert "失败原因" in payload["reply"]["content"]
    assert "不可用" in payload["reply"]["content"]
    assert payload["handoff_status"] == "ai_active"
    assert payload["tool_calls"] == []
    assert payload["sources"] == []


def test_chat_endpoint_returns_mock_skill_tool_call(monkeypatch) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "fake")
    client = TestClient(app)

    response = client.post(
        "/api/v1/chat",
        json=build_chat_payload("帮我查一下 EVER GIVEN 当前船位"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["handoff_status"] == "ai_active"
    assert payload["tool_calls"] == [
        {
            "tool_name": "ship.position.query",
            "status": "mocked",
            "input_payload": {"keyword": "EVER GIVEN"},
            "output_payload": {"result": "mocked_skill_execution"},
        }
    ]
    assert payload["sources"] == []


def test_chat_endpoint_returns_faq_source(monkeypatch) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "fake")
    client = TestClient(app)

    response = client.post(
        "/api/v1/chat",
        json=build_chat_payload("Hifleet 如何查询船位？"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert "船位查询" in payload["reply"]["content"]
    assert payload["tool_calls"] == []
    assert payload["sources"] == [
        {
            "source_type": "faq",
            "title": "Hifleet FAQ",
            "snippet": "船位查询支持按船名、IMO、MMSI 检索。",
        }
    ]
