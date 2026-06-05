from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from backend.app.agent.model_gateway import ModelGateway
from backend.app.api.conversations import get_conversation_service
from backend.app.agent.supervisor import SupervisorRouter
from backend.app.schemas.model import ModelGatewayRequest, ModelGatewayResponse, ModelMessage
from backend.app.schemas.supervisor import SupervisorDecision, SupervisorMessage
from backend.app.services.conversation_service import ConversationService

router = APIRouter(prefix="/chat", tags=["chat"])


def get_supervisor_router() -> SupervisorRouter:
    return SupervisorRouter()


def get_model_gateway() -> ModelGateway:
    return ModelGateway.from_settings()


def get_optional_conversation_service() -> ConversationService | None:
    try:
        return get_conversation_service()
    except Exception:
        return None


class ChatUserRequest(BaseModel):
    user_id: str | None = None
    display_name: str | None = None


class ChatMessageRequest(BaseModel):
    type: str
    content: str
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    channel_type: str
    user: ChatUserRequest | None = None
    message: ChatMessageRequest
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatReplyResponse(BaseModel):
    type: str = "text"
    content: str


class ChatToolCallResponse(BaseModel):
    tool_name: str
    status: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] | None = None


class ChatSourceResponse(BaseModel):
    source_type: str
    title: str
    snippet: str


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    reply: ChatReplyResponse
    handoff_status: str
    tool_calls: list[ChatToolCallResponse]
    sources: list[ChatSourceResponse]
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


@router.post("", response_model=ChatResponse)
def create_chat_completion(
    payload: ChatRequest,
    supervisor: SupervisorRouter = Depends(get_supervisor_router),
    model_gateway: ModelGateway = Depends(get_model_gateway),
    conversation_service: ConversationService | None = Depends(get_optional_conversation_service),
) -> ChatResponse:
    conversation_id = payload.conversation_id or str(uuid.uuid4())
    decision = supervisor.route(
        SupervisorMessage(
            message_type=payload.message.type,
            content=payload.message.content,
            attachments=payload.message.attachments,
            metadata=payload.metadata,
        )
    )

    reply, tool_calls, sources, model_response = _build_chat_artifacts(
        payload=payload,
        conversation_id=conversation_id,
        supervisor_decision=decision,
        model_gateway=model_gateway,
    )
    persistence_status = "skipped"
    persistence_error: str | None = None
    handoff_status = decision.handoff_status
    persisted_message_id: str | None = None

    if conversation_service is None:
        persistence_status = "best_effort_unavailable"
        persistence_error = "Conversation persistence service is unavailable in the current runtime."
    else:
        try:
            conversation = _resolve_conversation(
                payload=payload,
                requested_conversation_id=conversation_id,
                conversation_service=conversation_service,
            )
            conversation_id = conversation.id
            user_message = conversation_service.append_message(
                conversation_id=conversation_id,
                sender_type="user",
                message_type=payload.message.type,
                content=payload.message.content,
                content_payload={"attachments": payload.message.attachments},
            )

            if decision.intent == "handoff_required":
                conversation = conversation_service.request_handoff(
                    conversation_id=conversation_id,
                    reason=decision.reason,
                )
                handoff_status = conversation.handoff_status

            assistant_message = conversation_service.append_message(
                conversation_id=conversation_id,
                sender_type="assistant",
                message_type="text",
                content=reply,
                content_payload={
                    "sources": [source.model_dump() for source in sources],
                    "tool_calls": [tool_call.model_dump() for tool_call in tool_calls],
                    "intent": decision.intent,
                },
            )
            persisted_message_id = assistant_message.id

            for tool_call in tool_calls:
                conversation_service.create_tool_call(
                    conversation_id=conversation_id,
                    message_id=user_message.id,
                    tool_name=tool_call.tool_name,
                    status=_tool_call_status_for_storage(tool_call.status),
                    input_payload=tool_call.input_payload,
                    output_payload=tool_call.output_payload,
                    error_message=_tool_call_error_message(tool_call),
                )

            if model_response is not None:
                usage = model_response.usage
                conversation_service.create_model_call(
                    conversation_id=conversation_id,
                    message_id=assistant_message.id,
                    provider=model_response.provider,
                    model_name=model_response.model_name,
                    status="success" if model_response.status == "success" else "failed",
                    prompt_tokens=usage.prompt_tokens if usage is not None else None,
                    completion_tokens=usage.completion_tokens if usage is not None else None,
                    latency_ms=model_response.latency_ms,
                    error_message=model_response.error.message if model_response.error else None,
                )

            conversation_service.update_conversation_overview(
                conversation_id=conversation_id,
                title=conversation.title or _build_conversation_title(payload.message.content),
                summary=_build_conversation_summary(reply=reply),
                metadata={
                    "last_intent": decision.intent,
                    "last_target": decision.target,
                    "last_source": payload.metadata.get("source", "chat_api"),
                },
            )
            persistence_status = "persisted"
        except Exception as exc:
            persistence_status = "best_effort_failed"
            persistence_error = str(exc)

    return ChatResponse(
        conversation_id=conversation_id,
        message_id=persisted_message_id or str(uuid.uuid4()),
        reply=ChatReplyResponse(content=reply),
        handoff_status=handoff_status,
        tool_calls=tool_calls,
        sources=sources,
        metadata={
            "intent": decision.intent,
            "target": decision.target,
            "reason": decision.reason,
            "persistence_status": persistence_status,
            **({"persistence_error": persistence_error} if persistence_error else {}),
        },
    )


def _build_chat_artifacts(
    *,
    payload: ChatRequest,
    conversation_id: str,
    supervisor_decision: SupervisorDecision,
    model_gateway: ModelGateway,
) -> tuple[
    str,
    list[ChatToolCallResponse],
    list[ChatSourceResponse],
    ModelGatewayResponse | None,
]:
    if _is_failure_mode_question(payload.message.content):
        return (
            "失败原因: 当前模型或服务可能不可用，MVP 聊天入口不会伪造真实模型调用结果，请稍后重试或联系人工处理。",
            [],
            [],
            None,
        )

    if supervisor_decision.intent == "handoff_required":
        return (
            "已识别人工协助请求，当前会话将保持记录并等待人工客服接入。",
            [],
            [],
            None,
        )

    if supervisor_decision.intent == "faq":
        return (
            "Hifleet 船位查询可通过船名、IMO 或 MMSI 发起，结果会结合平台知识说明返回。",
            [],
            [
                ChatSourceResponse(
                    source_type="faq",
                    title="Hifleet FAQ",
                    snippet="船位查询支持按船名、IMO、MMSI 检索。",
                )
            ],
            None,
        )

    if supervisor_decision.intent == "skill_candidate":
        skill_plan = supervisor_decision.skill_candidate
        assert skill_plan is not None
        if skill_plan.missing_arguments:
            return (
                "当前识别到技能调用请求，但仍缺少关键参数，请补充船名或检索关键词。",
                [
                    ChatToolCallResponse(
                        tool_name=skill_plan.skill_name,
                        status="missing_arguments",
                        input_payload=skill_plan.arguments,
                        output_payload={"missing_arguments": skill_plan.missing_arguments},
                    )
                ],
                [],
                None,
            )

        return (
            f"已按 MVP 模式记录技能调用请求，目标关键词为 {skill_plan.arguments.get('keyword', '未提供')}。",
            [
                ChatToolCallResponse(
                    tool_name=skill_plan.skill_name,
                    status="mocked",
                    input_payload=skill_plan.arguments,
                    output_payload={"result": "mocked_skill_execution"},
                )
            ],
            [],
            None,
        )

    if supervisor_decision.intent == "web_research":
        return (
            "当前 MVP 仅返回结构化路由结果，公开网页检索暂未在该聊天入口执行。",
            [],
            [],
            None,
        )

    if supervisor_decision.intent == "image_understanding":
        return (
            "当前 MVP 尚未在该聊天入口启用图片理解能力，请改用后续多模态链路。",
            [],
            [],
            None,
        )

    gateway_response = model_gateway.generate(
        ModelGatewayRequest(
            messages=[
                ModelMessage(role="system", content="You are the Hifleet AI customer service assistant."),
                ModelMessage(role="user", content=payload.message.content),
            ],
            metadata={
                "conversation_id": conversation_id,
                "channel_type": payload.channel_type,
                **payload.metadata,
            },
        )
    )
    if gateway_response.status == "success" and gateway_response.output_text:
        return gateway_response.output_text, [], [], gateway_response

    error_message = "模型服务当前不可用。"
    if gateway_response.error is not None and gateway_response.error.message:
        error_message = gateway_response.error.message
    return (
        f"失败原因: {error_message} 请稍后重试或联系人工处理。",
        [],
        [],
        gateway_response,
    )


def _is_failure_mode_question(content: str) -> bool:
    return "不可用" in content and ("模型" in content or "服务" in content)


def _resolve_conversation(
    *,
    payload: ChatRequest,
    requested_conversation_id: str,
    conversation_service: ConversationService,
):
    if payload.conversation_id:
        conversation = conversation_service.get_conversation(conversation_id=payload.conversation_id)
        if conversation is not None:
            return conversation
    return conversation_service.create_conversation(
        channel_type=payload.channel_type,
        title=_build_conversation_title(payload.message.content),
        user_id=payload.user.user_id if payload.user else None,
        metadata={
            "source": payload.metadata.get("source", "chat_api"),
            "requested_conversation_id": requested_conversation_id,
            **payload.metadata,
        },
    )


def _build_conversation_title(content: str) -> str:
    stripped = " ".join(content.split()).strip()
    if not stripped:
        return "Test chat conversation"
    return stripped[:80]


def _build_conversation_summary(*, reply: str) -> str:
    stripped = " ".join(reply.split()).strip()
    return stripped[:160]


def _tool_call_status_for_storage(status: str) -> str:
    if status == "missing_arguments":
        return "skipped"
    return "success"


def _tool_call_error_message(tool_call: ChatToolCallResponse) -> str | None:
    if tool_call.status != "missing_arguments":
        return None
    if tool_call.output_payload and tool_call.output_payload.get("missing_arguments"):
        missing_arguments = tool_call.output_payload["missing_arguments"]
        if isinstance(missing_arguments, list):
            return f"Missing arguments: {', '.join(str(item) for item in missing_arguments)}"
    return "Missing arguments"
