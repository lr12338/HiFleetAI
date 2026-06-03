from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import Base, create_engine_for_url
from backend.app.main import create_app
from backend.app.models import Conversation, HandoffEvent
from backend.app.services.conversation_service import ConversationService


def build_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine_for_url(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def build_client(tmp_path):
    from backend.app.api.conversations import get_conversation_service
    from backend.app.auth.dependencies import get_auth_service
    from backend.app.auth.service import AuthService

    database_url = f"sqlite:///{tmp_path / 'handoff-api-test.db'}"
    session_factory = build_session_factory(database_url)
    auth_service = AuthService(
        session_factory=session_factory,
        jwt_secret="unit-test-secret-key-with-32-bytes",
        access_token_expire_minutes=15,
    )
    user = auth_service.create_local_user(
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
    return client, auth_service, conversation_service, session_factory, user.id


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


def create_open_conversation(conversation_service: ConversationService) -> str:
    conversation = conversation_service.create_conversation(
        channel_type="console",
        title="Handoff API test",
        metadata={"source": "pytest-handoff"},
    )
    return conversation.id


def test_handoff_pause_resume_success_flow_records_events(tmp_path) -> None:
    client, _, conversation_service, session_factory, operator_id = build_client(tmp_path)
    conversation_id = create_open_conversation(conversation_service)
    access_token = login(client)
    headers = {"Authorization": f"Bearer {access_token}"}

    handoff_response = client.post(
        f"/api/v1/conversations/{conversation_id}/handoff",
        json={"reason": "用户要求人工客服", "operator_id": operator_id},
        headers=headers,
    )
    assert handoff_response.status_code == 200
    assert handoff_response.json() == {
        "conversation_id": conversation_id,
        "handoff_status": "human_active",
        "assigned_agent_id": operator_id,
        "event_type": "takeover",
    }

    pause_response = client.post(
        f"/api/v1/conversations/{conversation_id}/pause-ai",
        json={"reason": "人工处理中，暂停 AI"},
        headers=headers,
    )
    assert pause_response.status_code == 200
    assert pause_response.json() == {
        "conversation_id": conversation_id,
        "handoff_status": "ai_paused",
        "assigned_agent_id": operator_id,
        "event_type": "pause_ai",
    }

    resume_response = client.post(
        f"/api/v1/conversations/{conversation_id}/resume-ai",
        json={"reason": "处理完成，恢复 AI"},
        headers=headers,
    )
    assert resume_response.status_code == 200
    assert resume_response.json() == {
        "conversation_id": conversation_id,
        "handoff_status": "ai_active",
        "assigned_agent_id": None,
        "event_type": "resume_ai",
    }

    with session_factory() as session:
        conversation = session.get(Conversation, conversation_id)
        assert conversation is not None
        assert conversation.handoff_status == "ai_active"
        assert conversation.assigned_agent_id is None

        events = list(
            session.scalars(
                select(HandoffEvent)
                .where(HandoffEvent.conversation_id == conversation_id)
                .order_by(HandoffEvent.created_at.asc(), HandoffEvent.id.asc())
            ).all()
        )
        assert [(event.event_type, event.operator_id, event.reason) for event in events] == [
            ("takeover", operator_id, "用户要求人工客服"),
            ("pause_ai", operator_id, "人工处理中，暂停 AI"),
            ("resume_ai", operator_id, "处理完成，恢复 AI"),
        ]


def test_handoff_api_rejects_illegal_state_transition(tmp_path) -> None:
    client, _, conversation_service, _, _ = build_client(tmp_path)
    conversation_id = create_open_conversation(conversation_service)
    access_token = login(client)

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/resume-ai",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Cannot transition conversation from 'ai_active' to 'ai_active'."
    }


def test_handoff_endpoints_require_login(tmp_path) -> None:
    client, _, conversation_service, _, _ = build_client(tmp_path)
    conversation_id = create_open_conversation(conversation_service)

    endpoints = (
        f"/api/v1/conversations/{conversation_id}/handoff",
        f"/api/v1/conversations/{conversation_id}/pause-ai",
        f"/api/v1/conversations/{conversation_id}/resume-ai",
    )

    for endpoint in endpoints:
        response = client.post(endpoint)
        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}


def test_handoff_endpoints_return_404_for_missing_conversation(tmp_path) -> None:
    client, _, _, _, _ = build_client(tmp_path)
    access_token = login(client)
    headers = {"Authorization": f"Bearer {access_token}"}
    conversation_id = "00000000-0000-0000-0000-000000000000"

    endpoints = (
        f"/api/v1/conversations/{conversation_id}/handoff",
        f"/api/v1/conversations/{conversation_id}/pause-ai",
        f"/api/v1/conversations/{conversation_id}/resume-ai",
    )

    for endpoint in endpoints:
        response = client.post(endpoint, headers=headers)
        assert response.status_code == 404
        assert response.json() == {
            "detail": "Conversation '00000000-0000-0000-0000-000000000000' was not found"
        }
