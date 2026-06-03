from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.models import Conversation, Message, ModelCall, ToolCall


ALLOWED_CHANNEL_TYPES = {"console", "chatwoot", "wechat_kf", "wechat_official"}
ALLOWED_SENDER_TYPES = {"assistant", "human_agent", "system", "user"}
ALLOWED_MESSAGE_TYPES = {"file", "image", "system", "text", "voice"}
DEFAULT_SEND_STATUS_BY_SENDER = {
    "assistant": "sent",
    "human_agent": "sent",
    "system": "sent",
    "user": "received",
}


class ConversationService:
    def __init__(self, *, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create_conversation(
        self,
        *,
        channel_type: str,
        title: str | None = None,
        user_id: str | None = None,
        metadata: dict | None = None,
    ) -> Conversation:
        self._validate_channel_type(channel_type)

        conversation = Conversation(
            user_id=user_id,
            channel_type=channel_type,
            title=title,
            metadata_json=None if metadata is None else dict(metadata),
        )

        with self._session_factory() as session:
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            return conversation

    def get_conversation(self, *, conversation_id: str) -> Conversation | None:
        with self._session_factory() as session:
            return session.get(Conversation, conversation_id)

    def append_message(
        self,
        *,
        conversation_id: str,
        sender_type: str,
        message_type: str,
        content: str | None = None,
        content_payload: dict | None = None,
        sender_id: str | None = None,
        channel_message_id: str | None = None,
        send_status: str | None = None,
        created_at: datetime | None = None,
    ) -> Message:
        self._validate_sender_type(sender_type)
        self._validate_message_type(message_type)

        message_created_at = self._normalize_datetime(created_at or datetime.now(UTC))

        with self._session_factory() as session:
            conversation = self._get_conversation_or_raise(
                session=session,
                conversation_id=conversation_id,
            )
            message = Message(
                conversation_id=conversation_id,
                sender_type=sender_type,
                sender_id=sender_id,
                message_type=message_type,
                content=content,
                content_payload=None if content_payload is None else dict(content_payload),
                channel_message_id=channel_message_id,
                send_status=send_status or DEFAULT_SEND_STATUS_BY_SENDER[sender_type],
                created_at=message_created_at,
            )
            session.add(message)
            conversation.last_message_at = self._latest_message_at(
                current_value=conversation.last_message_at,
                candidate_value=message_created_at,
            )
            session.commit()
            session.refresh(message)
            return message

    def get_timeline(self, *, conversation_id: str) -> list[Message]:
        with self._session_factory() as session:
            self._get_conversation_or_raise(session=session, conversation_id=conversation_id)
            statement = (
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc(), Message.id.asc())
            )
            return list(session.scalars(statement).all())

    def list_conversations(
        self,
        *,
        status: str | None = None,
        channel_type: str | None = None,
        keyword: str | None = None,
    ) -> list[Conversation]:
        with self._session_factory() as session:
            statement = select(Conversation)

            normalized_status = self._normalize_filter_value(status)
            if normalized_status is not None:
                statement = statement.where(Conversation.status == normalized_status)

            normalized_channel_type = self._normalize_filter_value(channel_type)
            if normalized_channel_type is not None:
                statement = statement.where(Conversation.channel_type == normalized_channel_type)

            normalized_keyword = self._normalize_filter_value(keyword)
            if normalized_keyword is not None:
                search_term = f"%{normalized_keyword.lower()}%"
                statement = statement.where(
                    or_(
                        func.lower(func.coalesce(Conversation.title, "")).like(search_term),
                        func.lower(func.coalesce(Conversation.summary, "")).like(search_term),
                    )
                )

            activity_timestamp = func.coalesce(
                Conversation.last_message_at,
                Conversation.updated_at,
                Conversation.created_at,
            )
            statement = statement.order_by(activity_timestamp.desc(), Conversation.id.desc())
            return list(session.scalars(statement).all())

    def get_tool_calls(self, *, conversation_id: str) -> list[ToolCall]:
        with self._session_factory() as session:
            self._get_conversation_or_raise(session=session, conversation_id=conversation_id)
            statement = (
                select(ToolCall)
                .where(ToolCall.conversation_id == conversation_id)
                .order_by(ToolCall.created_at.asc(), ToolCall.id.asc())
            )
            return list(session.scalars(statement).all())

    def get_failed_tool_calls(self, *, conversation_id: str) -> list[ToolCall]:
        with self._session_factory() as session:
            self._get_conversation_or_raise(session=session, conversation_id=conversation_id)
            statement = (
                select(ToolCall)
                .where(
                    ToolCall.conversation_id == conversation_id,
                    or_(ToolCall.status != "success", ToolCall.error_message.is_not(None)),
                )
                .order_by(ToolCall.created_at.asc(), ToolCall.id.asc())
            )
            return list(session.scalars(statement).all())

    def get_failed_model_calls(self, *, conversation_id: str) -> list[ModelCall]:
        with self._session_factory() as session:
            self._get_conversation_or_raise(session=session, conversation_id=conversation_id)
            statement = (
                select(ModelCall)
                .where(
                    ModelCall.conversation_id == conversation_id,
                    or_(ModelCall.status != "success", ModelCall.error_message.is_not(None)),
                )
                .order_by(ModelCall.created_at.asc(), ModelCall.id.asc())
            )
            return list(session.scalars(statement).all())

    @staticmethod
    def _validate_channel_type(channel_type: str) -> None:
        if channel_type not in ALLOWED_CHANNEL_TYPES:
            raise ValueError(f"Unsupported channel_type '{channel_type}'.")

    @staticmethod
    def _validate_sender_type(sender_type: str) -> None:
        if sender_type not in ALLOWED_SENDER_TYPES:
            raise ValueError(f"Unsupported sender_type '{sender_type}'.")

    @staticmethod
    def _validate_message_type(message_type: str) -> None:
        if message_type not in ALLOWED_MESSAGE_TYPES:
            raise ValueError(f"Unsupported message_type '{message_type}'.")

    @staticmethod
    def _normalize_filter_value(value: str | None) -> str | None:
        if value is None:
            return None
        normalized_value = value.strip()
        if not normalized_value:
            return None
        return normalized_value

    @staticmethod
    def _get_conversation_or_raise(*, session: Session, conversation_id: str) -> Conversation:
        conversation = session.get(Conversation, conversation_id)
        if conversation is None:
            raise ValueError(f"Conversation '{conversation_id}' does not exist.")
        return conversation

    @staticmethod
    def _latest_message_at(*, current_value: object | None, candidate_value: datetime) -> datetime:
        normalized_current = ConversationService._normalize_datetime(current_value)
        if normalized_current is not None and normalized_current > candidate_value:
            return normalized_current
        return candidate_value

    @staticmethod
    def _normalize_datetime(value: object | None) -> datetime | None:
        if not isinstance(value, datetime):
            return None
        if value.tzinfo is None:
            return value
        return value.astimezone(UTC).replace(tzinfo=None)
