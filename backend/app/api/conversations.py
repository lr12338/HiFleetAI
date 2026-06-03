from __future__ import annotations

from functools import lru_cache
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session, sessionmaker

from backend.app.auth.dependencies import get_current_principal
from backend.app.auth.service import AuthenticatedPrincipal
from backend.app.core.config import get_settings
from backend.app.db import create_session_factory
from backend.app.services import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@lru_cache
def get_conversation_session_factory() -> sessionmaker[Session]:
    settings = get_settings()
    return create_session_factory(settings.database_url)


def get_conversation_service() -> ConversationService:
    return ConversationService(session_factory=get_conversation_session_factory())


class ConversationListItemResponse(BaseModel):
    id: str
    channel_type: str
    title: str | None
    status: str
    handoff_status: str
    summary: str | None
    last_message_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationListResponse(BaseModel):
    items: list[ConversationListItemResponse]
    total: int


@router.get("", response_model=ConversationListResponse)
def list_conversations(
    status: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    _: AuthenticatedPrincipal = Depends(get_current_principal),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ConversationListResponse:
    conversations = conversation_service.list_conversations(
        status=status,
        channel_type=channel,
        keyword=keyword,
    )
    return ConversationListResponse(
        items=[ConversationListItemResponse.model_validate(item) for item in conversations],
        total=len(conversations),
    )
