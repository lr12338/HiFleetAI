from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import Base, create_engine_for_url
from backend.app.main import create_app
from backend.app.models import Conversation
from backend.app.services.conversation_service import ConversationService


def build_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine_for_url(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def build_client(tmp_path):
    from backend.app.api.conversations import get_conversation_service
    from backend.app.auth.dependencies import get_auth_service
    from backend.app.auth.service import AuthService

    database_url = f"sqlite:///{tmp_path / 'conversation-list-test.db'}"
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


def seed_conversations(
    conversation_service: ConversationService,
    session_factory: sessionmaker[Session],
) -> list[str]:
    base_time = datetime(2026, 6, 3, 12, 0, tzinfo=UTC)

    alpha = conversation_service.create_conversation(
        channel_type="console",
        title="Alpha cargo issue",
        metadata={"source": "pytest"},
    )
    conversation_service.append_message(
        conversation_id=alpha.id,
        sender_type="user",
        message_type="text",
        content="Alpha first message",
        created_at=base_time,
    )

    bravo = conversation_service.create_conversation(
        channel_type="chatwoot",
        title="Bravo handoff request",
        metadata={"source": "pytest"},
    )
    conversation_service.append_message(
        conversation_id=bravo.id,
        sender_type="user",
        message_type="text",
        content="Bravo first message",
        created_at=base_time + timedelta(minutes=5),
    )

    charlie = conversation_service.create_conversation(
        channel_type="console",
        title="General support",
        metadata={"source": "pytest"},
    )
    conversation_service.append_message(
        conversation_id=charlie.id,
        sender_type="assistant",
        message_type="text",
        content="Charlie reply",
        created_at=base_time + timedelta(minutes=10),
    )

    with session_factory() as session:
        alpha_record = session.get(Conversation, alpha.id)
        bravo_record = session.get(Conversation, bravo.id)
        charlie_record = session.get(Conversation, charlie.id)
        assert alpha_record is not None
        assert bravo_record is not None
        assert charlie_record is not None

        alpha_record.summary = "Customer asked about cargo visibility."
        bravo_record.summary = "Needs human handoff for billing."
        bravo_record.status = "closed"
        charlie_record.summary = "Routine support follow-up."
        session.commit()

    return [alpha.id, bravo.id, charlie.id]


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


def test_conversation_list_requires_login(tmp_path) -> None:
    client, _, _, _ = build_client(tmp_path)

    response = client.get("/api/v1/conversations")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_conversation_list_returns_authenticated_results(tmp_path) -> None:
    client, _, conversation_service, session_factory = build_client(tmp_path)
    seeded_ids = seed_conversations(conversation_service, session_factory)
    access_token = login(client)

    response = client.get(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert [item["id"] for item in payload["items"]] == [seeded_ids[2], seeded_ids[1], seeded_ids[0]]
    assert payload["items"][0]["channel_type"] == "console"
    assert payload["items"][0]["status"] == "open"
    assert payload["items"][1]["channel_type"] == "chatwoot"
    assert payload["items"][1]["status"] == "closed"


def test_conversation_list_filters_by_status(tmp_path) -> None:
    client, _, conversation_service, session_factory = build_client(tmp_path)
    seeded_ids = seed_conversations(conversation_service, session_factory)
    access_token = login(client)

    response = client.get(
        "/api/v1/conversations",
        params={"status": "closed"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert [item["id"] for item in payload["items"]] == [seeded_ids[1]]


def test_conversation_list_filters_by_channel(tmp_path) -> None:
    client, _, conversation_service, session_factory = build_client(tmp_path)
    seeded_ids = seed_conversations(conversation_service, session_factory)
    access_token = login(client)

    response = client.get(
        "/api/v1/conversations",
        params={"channel": "chatwoot"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert [item["id"] for item in payload["items"]] == [seeded_ids[1]]


def test_conversation_list_filters_by_keyword(tmp_path) -> None:
    client, _, conversation_service, session_factory = build_client(tmp_path)
    seed_conversations(conversation_service, session_factory)
    access_token = login(client)

    response = client.get(
        "/api/v1/conversations",
        params={"keyword": "billing"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["title"] == "Bravo handoff request"
    assert payload["items"][0]["summary"] == "Needs human handoff for billing."
