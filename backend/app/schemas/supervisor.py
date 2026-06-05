from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


SupervisorIntent = Literal[
    "faq",
    "web_research",
    "image_understanding",
    "skill_candidate",
    "handoff_required",
    "general_chat",
]
SupervisorTarget = Literal[
    "knowledge_hub",
    "deep_search_hub",
    "multimodal_processor",
    "skill_hub",
    "human_handoff_service",
    "model_gateway",
]
HandoffStatus = Literal["ai_active", "human_pending"]
ExecutionMode = Literal["route_only"]
MessageType = Literal["text", "image", "voice", "file"]


@dataclass(frozen=True)
class SupervisorMessage:
    message_type: MessageType
    content: str
    attachments: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def has_image_input(self) -> bool:
        if self.message_type == "image":
            return True
        return any(attachment.get("type") == "image" for attachment in self.attachments)


@dataclass(frozen=True)
class SkillCandidatePlan:
    skill_name: str
    arguments: dict[str, str] = field(default_factory=dict)
    missing_arguments: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SupervisorDecision:
    intent: SupervisorIntent
    target: SupervisorTarget
    reason: str
    handoff_status: HandoffStatus
    execution_mode: ExecutionMode = "route_only"
    allow_direct_tool_execution: bool = False
    requires_sources: bool = False
    skill_candidate: SkillCandidatePlan | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
