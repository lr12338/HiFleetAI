from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import Base, create_engine_for_url
from backend.app.main import create_app
from backend.app.models import Conversation, ModelCall, ToolCall
from backend.app.services.conversation_service import ConversationService


def build_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine_for_url(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def build_client(tmp_path):
    from backend.app.api.conversations import get_conversation_service
    from backend.app.auth.dependencies import get_auth_service
    from backend.app.auth.service import AuthService

    database_url = f"sqlite:///{tmp_path / 'conversation-detail-test.db'}"
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

    conversation_service = ConversationService(session_factory=session_factory)
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_conversation_service] = lambda: conversation_service
    client = TestClient(app)
    return client, auth_service, conversation_service, session_factory


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


def seed_detail_conversation(
    conversation_service: ConversationService,
    session_factory: sessionmaker[Session],
) -> str:
    base_time = datetime(2026, 6, 3, 12, 0, tzinfo=UTC)
    conversation = conversation_service.create_conversation(
        channel_type="console",
        title="Conversation detail test",
        metadata={"source": "pytest-detail"},
    )

    first_message = conversation_service.append_message(
        conversation_id=conversation.id,
        sender_type="user",
        message_type="text",
        content="First user question",
        created_at=base_time,
    )
    second_message = conversation_service.append_message(
        conversation_id=conversation.id,
        sender_type="assistant",
        message_type="text",
        content="Assistant answer",
        created_at=base_time + timedelta(minutes=1),
    )
    conversation_service.append_message(
        conversation_id=conversation.id,
        sender_type="system",
        message_type="system",
        content="System note",
        created_at=base_time + timedelta(minutes=2),
    )

    with session_factory() as session:
        conversation_record = session.get(Conversation, conversation.id)
        assert conversation_record is not None
        conversation_record.summary = "Seeded conversation for detail endpoint."

        session.add(
            ToolCall(
                conversation_id=conversation.id,
                message_id=first_message.id,
                tool_name="knowledge.search",
                input_payload={"query": "cargo visibility"},
                output_payload={"results": []},
                status="success",
                latency_ms=120,
                error_message=None,
                created_at=base_time + timedelta(seconds=30),
            )
        )
        session.add(
            ModelCall(
                conversation_id=conversation.id,
                message_id=second_message.id,
                provider="fake",
                model_name="fake-chat",
                prompt_tokens=12,
                completion_tokens=18,
                latency_ms=80,
                status="failed",
                error_message="Synthetic model failure",
                created_at=base_time + timedelta(minutes=1, seconds=15),
            )
        )
        session.commit()

    return conversation.id


def test_conversation_detail_requires_login(tmp_path) -> None:
    client, _, _, _ = build_client(tmp_path)

    response = client.get("/api/v1/conversations/test-conversation-id")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_conversation_detail_returns_authenticated_payload(tmp_path) -> None:
    client, _, conversation_service, session_factory = build_client(tmp_path)
    conversation_id = seed_detail_conversation(conversation_service, session_factory)
    access_token = login(client)

    response = client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == conversation_id
    assert payload["channel_type"] == "console"
    assert payload["title"] == "Conversation detail test"
    assert payload["summary"] == "Seeded conversation for detail endpoint."
    assert len(payload["messages"]) == 3
    assert payload["messages"][0]["content"] == "First user question"
    assert payload["messages"][1]["content"] == "Assistant answer"
    assert payload["messages"][2]["content"] == "System note"
    assert payload["tool_calls"] == [
        {
            "id": payload["tool_calls"][0]["id"],
            "message_id": payload["messages"][0]["id"],
            "tool_name": "knowledge.search",
            "status": "success",
            "latency_ms": 120,
            "error_message": None,
            "created_at": payload["tool_calls"][0]["created_at"],
        }
    ]
    assert payload["error_context"] == {
        "model_errors": [
            {
                "id": payload["error_context"]["model_errors"][0]["id"],
                "message_id": payload["messages"][1]["id"],
                "source": "model_gateway",
                "code": "failed",
                "message": "Synthetic model failure",
                "created_at": payload["error_context"]["model_errors"][0]["created_at"],
            }
        ],
        "tool_errors": [],
    }


def test_conversation_detail_returns_messages_in_timeline_order(tmp_path) -> None:
    client, _, conversation_service, session_factory = build_client(tmp_path)
    conversation_id = seed_detail_conversation(conversation_service, session_factory)
    access_token = login(client)

    response = client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert [message["sender_type"] for message in payload["messages"]] == [
        "user",
        "assistant",
        "system",
    ]
    assert [message["content"] for message in payload["messages"]] == [
        "First user question",
        "Assistant answer",
        "System note",
    ]


def test_conversation_detail_returns_structured_empty_sections_when_no_data(tmp_path) -> None:
    client, _, conversation_service, _ = build_client(tmp_path)
    conversation = conversation_service.create_conversation(
        channel_type="console",
        title="Empty detail sections",
        metadata={"source": "pytest-empty-detail"},
    )
    access_token = login(client)

    response = client.get(
        f"/api/v1/conversations/{conversation.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["messages"] == []
    assert payload["tool_calls"] == []
    assert payload["error_context"] == {
        "model_errors": [],
        "tool_errors": [],
    }


def test_conversation_detail_returns_404_for_missing_conversation(tmp_path) -> None:
    client, _, _, _ = build_client(tmp_path)
    access_token = login(client)

    response = client.get(
        "/api/v1/conversations/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Conversation '00000000-0000-0000-0000-000000000000' was not found"
    }
