from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import Base, create_engine_for_url
from backend.app.main import create_app
from backend.app.services.conversation_service import ConversationService


def build_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine_for_url(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def build_client(tmp_path):
    from backend.app.api.conversations import get_conversation_service
    from backend.app.auth.dependencies import get_auth_service
    from backend.app.auth.service import AuthService

    database_url = f"sqlite:///{tmp_path / 'notes-api-test.db'}"
    session_factory = build_session_factory(database_url)
    auth_service = AuthService(
        session_factory=session_factory,
        jwt_secret="unit-test-secret-key-with-32-bytes",
        access_token_expire_minutes=15,
    )
    admin_user = auth_service.create_local_user(
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
    return client, auth_service, conversation_service, admin_user.id


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


def seed_conversation(conversation_service: ConversationService) -> str:
    conversation = conversation_service.create_conversation(
        channel_type="console",
        title="Conversation notes test",
        metadata={"source": "pytest-notes"},
    )
    return conversation.id


@pytest.mark.parametrize(
    ("method", "url", "payload"),
    [
        ("get", "/api/v1/conversations/test-conversation-id/notes", None),
        ("post", "/api/v1/conversations/test-conversation-id/notes", {"content": "Internal note"}),
    ],
)
def test_notes_endpoints_require_login(tmp_path, method: str, url: str, payload: dict | None) -> None:
    client, _, _, _ = build_client(tmp_path)

    if method == "get":
        response = client.get(url)
    else:
        response = client.post(url, json=payload)

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_create_note_returns_created_record(tmp_path) -> None:
    client, _, conversation_service, admin_user_id = build_client(tmp_path)
    conversation_id = seed_conversation(conversation_service)
    access_token = login(client)

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/notes",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"content": "Need to follow up with carrier tomorrow."},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["conversation_id"] == conversation_id
    assert payload["author_id"] == admin_user_id
    assert payload["content"] == "Need to follow up with carrier tomorrow."
    assert payload["id"]
    assert payload["created_at"]


def test_list_notes_returns_notes_in_created_order(tmp_path) -> None:
    client, _, conversation_service, admin_user_id = build_client(tmp_path)
    conversation_id = seed_conversation(conversation_service)
    base_time = datetime(2026, 6, 3, 12, 0, tzinfo=UTC)
    conversation_service.create_note(
        conversation_id=conversation_id,
        author_id=admin_user_id,
        content="First internal note",
        created_at=base_time,
    )
    conversation_service.create_note(
        conversation_id=conversation_id,
        author_id=admin_user_id,
        content="Second internal note",
        created_at=base_time + timedelta(minutes=1),
    )
    access_token = login(client)

    response = client.get(
        f"/api/v1/conversations/{conversation_id}/notes",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert [note["content"] for note in payload["items"]] == [
        "First internal note",
        "Second internal note",
    ]
    assert all(note["conversation_id"] == conversation_id for note in payload["items"])


@pytest.mark.parametrize("method", ["get", "post"])
def test_notes_endpoints_return_404_for_missing_conversation(tmp_path, method: str) -> None:
    client, _, _, _ = build_client(tmp_path)
    access_token = login(client)
    url = "/api/v1/conversations/00000000-0000-0000-0000-000000000000/notes"

    if method == "get":
        response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    else:
        response = client.post(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            json={"content": "Missing conversation note"},
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Conversation '00000000-0000-0000-0000-000000000000' was not found"
    }
