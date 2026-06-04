from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.chat import get_optional_conversation_service
from backend.app.db import Base, create_engine_for_url
from backend.app.main import app, create_app
from backend.app.models import ModelCall
from backend.app.services.conversation_service import ConversationService


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


def build_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine_for_url(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def build_chat_client(tmp_path) -> tuple[TestClient, ConversationService, sessionmaker[Session], FastAPI]:
    database_url = f"sqlite:///{tmp_path / 'chat-api-test.db'}"
    session_factory = build_session_factory(database_url)
    conversation_service = ConversationService(session_factory=session_factory)
    local_app = create_app()
    local_app.dependency_overrides[get_optional_conversation_service] = lambda: conversation_service
    return TestClient(local_app), conversation_service, session_factory, local_app


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


def test_chat_endpoint_persists_conversation_messages_and_tool_call(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "fake")
    client, conversation_service, _, local_app = build_chat_client(tmp_path)

    response = client.post(
        "/api/v1/chat",
        json=build_chat_payload("帮我查一下 EVER GIVEN 当前船位"),
    )

    assert response.status_code == 200
    payload = response.json()
    conversation_id = payload["conversation_id"]
    assert payload["metadata"]["persistence_status"] == "persisted"

    conversation = conversation_service.get_conversation(conversation_id=conversation_id)
    assert conversation is not None
    assert conversation.title == "帮我查一下 EVER GIVEN 当前船位"
    assert conversation.summary == "已按 MVP 模式记录技能调用请求，目标关键词为 EVER GIVEN。"

    timeline = conversation_service.get_timeline(conversation_id=conversation_id)
    assert [message.sender_type for message in timeline] == ["user", "assistant"]
    assert [message.content for message in timeline] == [
        "帮我查一下 EVER GIVEN 当前船位",
        "已按 MVP 模式记录技能调用请求，目标关键词为 EVER GIVEN。",
    ]

    tool_calls = conversation_service.get_tool_calls(conversation_id=conversation_id)
    assert len(tool_calls) == 1
    assert tool_calls[0].tool_name == "ship.position.query"
    assert tool_calls[0].status == "success"
    assert tool_calls[0].output_payload == {"result": "mocked_skill_execution"}
    local_app.dependency_overrides.clear()


def test_chat_endpoint_persists_model_call_for_general_chat(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "fake")
    client, conversation_service, session_factory, local_app = build_chat_client(tmp_path)

    response = client.post(
        "/api/v1/chat",
        json=build_chat_payload("请介绍一下当前模型网关能力"),
    )

    assert response.status_code == 200
    payload = response.json()
    conversation_id = payload["conversation_id"]
    assert payload["metadata"]["persistence_status"] == "persisted"
    assert payload["reply"]["content"] == "Fake response: 请介绍一下当前模型网关能力"

    timeline = conversation_service.get_timeline(conversation_id=conversation_id)
    assert [message.sender_type for message in timeline] == ["user", "assistant"]

    with session_factory() as session:
        model_calls = session.scalars(
            select(ModelCall).where(ModelCall.conversation_id == conversation_id)
        ).all()
    assert len(model_calls) == 1
    assert model_calls[0].provider == "fake"
    assert model_calls[0].status == "success"
    assert model_calls[0].message_id == timeline[1].id
    local_app.dependency_overrides.clear()
