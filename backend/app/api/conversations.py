from __future__ import annotations

from functools import lru_cache
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, ConfigDict, StringConstraints
from sqlalchemy.orm import Session, sessionmaker

from backend.app.auth.dependencies import get_current_principal, require_roles
from backend.app.auth.service import AuthenticatedPrincipal
from backend.app.core.config import get_settings
from backend.app.db import create_session_factory
from backend.app.services import ConversationService
from backend.app.services.conversation_service import (
    ConversationNotFoundError,
    ConversationStateTransitionError,
)

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


class ConversationMessageResponse(BaseModel):
    id: str
    sender_type: str
    sender_id: str | None
    message_type: str
    content: str | None
    content_payload: dict | None
    send_status: str
    created_at: datetime


class ConversationToolCallSummaryResponse(BaseModel):
    id: str
    message_id: str | None
    tool_name: str
    status: str
    latency_ms: int | None
    error_message: str | None
    created_at: datetime


class ConversationModelErrorResponse(BaseModel):
    id: str
    message_id: str | None
    source: str
    code: str
    message: str | None
    created_at: datetime


class ConversationToolErrorResponse(BaseModel):
    id: str
    message_id: str | None
    source: str
    code: str
    message: str | None
    created_at: datetime
    tool_name: str | None


class ConversationErrorContextResponse(BaseModel):
    model_errors: list[ConversationModelErrorResponse]
    tool_errors: list[ConversationToolErrorResponse]


class ConversationDetailResponse(BaseModel):
    id: str
    user_id: str | None
    channel_type: str
    title: str | None
    status: str
    handoff_status: str
    assigned_agent_id: str | None
    summary: str | None
    metadata: dict | None
    last_message_at: datetime | None
    created_at: datetime
    updated_at: datetime
    messages: list[ConversationMessageResponse]
    tool_calls: list[ConversationToolCallSummaryResponse]
    error_context: ConversationErrorContextResponse


class ConversationNoteResponse(BaseModel):
    id: str
    conversation_id: str
    author_id: str | None
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationNoteListResponse(BaseModel):
    items: list[ConversationNoteResponse]
    total: int


class ConversationNoteCreateRequest(BaseModel):
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ConversationHandoffActionRequest(BaseModel):
    reason: str | None = None
    operator_id: str | None = None


class ConversationHandoffActionResponse(BaseModel):
    conversation_id: str
    handoff_status: str
    assigned_agent_id: str | None
    event_type: str


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


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation_detail(
    conversation_id: str = Path(...),
    _: AuthenticatedPrincipal = Depends(get_current_principal),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ConversationDetailResponse:
    conversation = conversation_service.get_conversation(conversation_id=conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation '{conversation_id}' was not found",
        )

    messages = conversation_service.get_timeline(conversation_id=conversation_id)
    tool_calls = conversation_service.get_tool_calls(conversation_id=conversation_id)
    model_errors = conversation_service.get_failed_model_calls(conversation_id=conversation_id)
    tool_errors = conversation_service.get_failed_tool_calls(conversation_id=conversation_id)

    return ConversationDetailResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        channel_type=conversation.channel_type,
        title=conversation.title,
        status=conversation.status,
        handoff_status=conversation.handoff_status,
        assigned_agent_id=conversation.assigned_agent_id,
        summary=conversation.summary,
        metadata=conversation.metadata_json,
        last_message_at=conversation.last_message_at,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            ConversationMessageResponse(
                id=message.id,
                sender_type=message.sender_type,
                sender_id=message.sender_id,
                message_type=message.message_type,
                content=message.content,
                content_payload=message.content_payload,
                send_status=message.send_status,
                created_at=message.created_at,
            )
            for message in messages
        ],
        tool_calls=[
            ConversationToolCallSummaryResponse(
                id=tool_call.id,
                message_id=tool_call.message_id,
                tool_name=tool_call.tool_name,
                status=tool_call.status,
                latency_ms=tool_call.latency_ms,
                error_message=tool_call.error_message,
                created_at=tool_call.created_at,
            )
            for tool_call in tool_calls
        ],
        error_context=ConversationErrorContextResponse(
            model_errors=[
                ConversationModelErrorResponse(
                    id=model_error.id,
                    message_id=model_error.message_id,
                    source="model_gateway",
                    code=model_error.status,
                    message=model_error.error_message,
                    created_at=model_error.created_at,
                )
                for model_error in model_errors
            ],
            tool_errors=[
                ConversationToolErrorResponse(
                    id=tool_error.id,
                    message_id=tool_error.message_id,
                    source="tool_call",
                    code=tool_error.status,
                    message=tool_error.error_message,
                    created_at=tool_error.created_at,
                    tool_name=tool_error.tool_name,
                )
                for tool_error in tool_errors
            ],
        ),
    )


@router.get("/{conversation_id}/notes", response_model=ConversationNoteListResponse)
def list_conversation_notes(
    conversation_id: str = Path(...),
    _: AuthenticatedPrincipal = Depends(get_current_principal),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ConversationNoteListResponse:
    try:
        notes = conversation_service.list_notes(conversation_id=conversation_id)
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' was not found",
        )

    return ConversationNoteListResponse(
        items=[ConversationNoteResponse.model_validate(note) for note in notes],
        total=len(notes),
    )


@router.post(
    "/{conversation_id}/notes",
    response_model=ConversationNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation_note(
    payload: ConversationNoteCreateRequest,
    conversation_id: str = Path(...),
    principal: AuthenticatedPrincipal = Depends(require_roles("admin", "agent")),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ConversationNoteResponse:
    try:
        note = conversation_service.create_note(
            conversation_id=conversation_id,
            author_id=principal.user_id,
            content=payload.content,
        )
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' was not found",
        )

    return ConversationNoteResponse.model_validate(note)


@router.post(
    "/{conversation_id}/handoff",
    response_model=ConversationHandoffActionResponse,
)
def handoff_conversation(
    conversation_id: str = Path(...),
    payload: ConversationHandoffActionRequest | None = None,
    principal: AuthenticatedPrincipal = Depends(require_roles("admin", "agent")),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ConversationHandoffActionResponse:
    operator_id = _resolve_operator_id(principal=principal, payload=payload)
    try:
        conversation = conversation_service.handoff_to_human(
            conversation_id=conversation_id,
            operator_id=operator_id,
            reason=None if payload is None else payload.reason,
        )
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' was not found",
        )
    except ConversationStateTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return ConversationHandoffActionResponse(
        conversation_id=conversation.id,
        handoff_status=conversation.handoff_status,
        assigned_agent_id=conversation.assigned_agent_id,
        event_type="takeover",
    )


@router.post(
    "/{conversation_id}/pause-ai",
    response_model=ConversationHandoffActionResponse,
)
def pause_conversation_ai(
    conversation_id: str = Path(...),
    payload: ConversationHandoffActionRequest | None = None,
    principal: AuthenticatedPrincipal = Depends(require_roles("admin", "agent")),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ConversationHandoffActionResponse:
    operator_id = _resolve_operator_id(principal=principal, payload=payload)
    try:
        conversation = conversation_service.pause_ai(
            conversation_id=conversation_id,
            operator_id=operator_id,
            reason=None if payload is None else payload.reason,
        )
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' was not found",
        )
    except ConversationStateTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return ConversationHandoffActionResponse(
        conversation_id=conversation.id,
        handoff_status=conversation.handoff_status,
        assigned_agent_id=conversation.assigned_agent_id,
        event_type="pause_ai",
    )


@router.post(
    "/{conversation_id}/resume-ai",
    response_model=ConversationHandoffActionResponse,
)
def resume_conversation_ai(
    conversation_id: str = Path(...),
    payload: ConversationHandoffActionRequest | None = None,
    principal: AuthenticatedPrincipal = Depends(require_roles("admin", "agent")),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ConversationHandoffActionResponse:
    operator_id = _resolve_operator_id(principal=principal, payload=payload)
    try:
        conversation = conversation_service.resume_ai(
            conversation_id=conversation_id,
            operator_id=operator_id,
            reason=None if payload is None else payload.reason,
        )
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' was not found",
        )
    except ConversationStateTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return ConversationHandoffActionResponse(
        conversation_id=conversation.id,
        handoff_status=conversation.handoff_status,
        assigned_agent_id=conversation.assigned_agent_id,
        event_type="resume_ai",
    )


def _resolve_operator_id(
    *,
    principal: AuthenticatedPrincipal,
    payload: ConversationHandoffActionRequest | None,
) -> str:
    if payload is None or payload.operator_id is None:
        return principal.user_id
    if payload.operator_id != principal.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="operator_id must match the authenticated user",
        )
    return payload.operator_id
