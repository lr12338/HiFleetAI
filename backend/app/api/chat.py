from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from backend.app.agent.model_gateway import ModelGateway
from backend.app.agent.supervisor import SupervisorRouter
from backend.app.schemas.model import ModelGatewayRequest, ModelMessage
from backend.app.schemas.supervisor import SupervisorDecision, SupervisorMessage

router = APIRouter(prefix="/chat", tags=["chat"])


def get_supervisor_router() -> SupervisorRouter:
    return SupervisorRouter()


def get_model_gateway() -> ModelGateway:
    return ModelGateway.from_settings()


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
) -> ChatResponse:
    conversation_id = payload.conversation_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    decision = supervisor.route(
        SupervisorMessage(
            message_type=payload.message.type,
            content=payload.message.content,
            attachments=payload.message.attachments,
            metadata=payload.metadata,
        )
    )

    reply, tool_calls, sources = _build_chat_artifacts(
        payload=payload,
        conversation_id=conversation_id,
        supervisor_decision=decision,
        model_gateway=model_gateway,
    )
    return ChatResponse(
        conversation_id=conversation_id,
        message_id=message_id,
        reply=ChatReplyResponse(content=reply),
        handoff_status=decision.handoff_status,
        tool_calls=tool_calls,
        sources=sources,
        metadata={
            "intent": decision.intent,
            "target": decision.target,
            "reason": decision.reason,
        },
    )


def _build_chat_artifacts(
    *,
    payload: ChatRequest,
    conversation_id: str,
    supervisor_decision: SupervisorDecision,
    model_gateway: ModelGateway,
) -> tuple[str, list[ChatToolCallResponse], list[ChatSourceResponse]]:
    if _is_failure_mode_question(payload.message.content):
        return (
            "失败原因: 当前模型或服务可能不可用，MVP 聊天入口不会伪造真实模型调用结果，请稍后重试或联系人工处理。",
            [],
            [],
        )

    if supervisor_decision.intent == "handoff_required":
        return (
            "已识别人工协助请求，当前会话将保持记录并等待人工客服接入。",
            [],
            [],
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
        )

    if supervisor_decision.intent == "web_research":
        return (
            "当前 MVP 仅返回结构化路由结果，公开网页检索暂未在该聊天入口执行。",
            [],
            [],
        )

    if supervisor_decision.intent == "image_understanding":
        return (
            "当前 MVP 尚未在该聊天入口启用图片理解能力，请改用后续多模态链路。",
            [],
            [],
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
        return gateway_response.output_text, [], []

    error_message = "模型服务当前不可用。"
    if gateway_response.error is not None and gateway_response.error.message:
        error_message = gateway_response.error.message
    return f"失败原因: {error_message} 请稍后重试或联系人工处理。", [], []


def _is_failure_mode_question(content: str) -> bool:
    return "不可用" in content and ("模型" in content or "服务" in content)
