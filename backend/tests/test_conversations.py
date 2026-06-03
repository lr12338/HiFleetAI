from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import Base, create_engine_for_url
from backend.app.models import Conversation, Message
from backend.app.services.conversation_service import ConversationService


def build_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine_for_url(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def test_create_console_conversation(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'conversation-service.db'}"
    session_factory = build_session_factory(database_url)
    service = ConversationService(session_factory=session_factory)

    conversation = service.create_conversation(
        channel_type="console",
        title="Console smoke session",
        metadata={"source": "pytest"},
    )

    assert isinstance(conversation, Conversation)
    assert conversation.channel_type == "console"
    assert conversation.title == "Console smoke session"
    assert conversation.status == "open"
    assert conversation.handoff_status == "ai_active"
    assert conversation.metadata_json == {"source": "pytest"}
    assert conversation.last_message_at is None


def test_append_messages_and_read_timeline_in_created_at_order(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'conversation-timeline.db'}"
    session_factory = build_session_factory(database_url)
    service = ConversationService(session_factory=session_factory)
    conversation = service.create_conversation(channel_type="console", title="Timeline test")

    started_at = datetime(2026, 6, 3, 12, 0, tzinfo=UTC)
    user_message = service.append_message(
        conversation_id=conversation.id,
        sender_type="user",
        message_type="text",
        content="你好，我想测试会话。",
        created_at=started_at,
    )
    assistant_message = service.append_message(
        conversation_id=conversation.id,
        sender_type="assistant",
        message_type="text",
        content="已收到，这是一条助手回复。",
        created_at=started_at + timedelta(minutes=1),
    )

    timeline = service.get_timeline(conversation_id=conversation.id)

    assert [message.id for message in timeline] == [user_message.id, assistant_message.id]
    assert [message.sender_type for message in timeline] == ["user", "assistant"]
    assert [message.content for message in timeline] == [
        "你好，我想测试会话。",
        "已收到，这是一条助手回复。",
    ]
    assert isinstance(user_message, Message)
    assert isinstance(assistant_message, Message)
    assert user_message.send_status == "received"
    assert assistant_message.send_status == "sent"

    refreshed_conversation = service.get_conversation(conversation_id=conversation.id)
    assert refreshed_conversation is not None
    assert refreshed_conversation.last_message_at == assistant_message.created_at
