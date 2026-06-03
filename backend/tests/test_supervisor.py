from __future__ import annotations

import pytest

from backend.app.agent.supervisor import SupervisorRouter
from backend.app.schemas.supervisor import SupervisorMessage


@pytest.fixture
def router() -> SupervisorRouter:
    return SupervisorRouter()


def test_routes_faq_queries_to_knowledge_flow(router: SupervisorRouter) -> None:
    decision = router.route(
        SupervisorMessage(
            message_type="text",
            content="Hifleet 怎么查询船位？",
        )
    )

    assert decision.intent == "faq"
    assert decision.target == "knowledge_hub"
    assert decision.handoff_status == "ai_active"
    assert decision.execution_mode == "route_only"
    assert decision.allow_direct_tool_execution is False
    assert decision.skill_candidate is None


def test_routes_web_research_queries_to_deep_search(router: SupervisorRouter) -> None:
    decision = router.route(
        SupervisorMessage(
            message_type="text",
            content="请检索并总结近期公开航运政策信息，给出来源。",
        )
    )

    assert decision.intent == "web_research"
    assert decision.target == "deep_search_hub"
    assert decision.requires_sources is True
    assert decision.execution_mode == "route_only"


def test_routes_image_messages_to_image_understanding(router: SupervisorRouter) -> None:
    decision = router.route(
        SupervisorMessage(
            message_type="image",
            content="请分析这张图片里有什么信息。",
            attachments=[{"type": "image", "path": "fixtures/sample.png"}],
        )
    )

    assert decision.intent == "image_understanding"
    assert decision.target == "multimodal_processor"
    assert decision.requires_sources is False
    assert decision.execution_mode == "route_only"


def test_routes_skill_candidate_with_extracted_keyword(router: SupervisorRouter) -> None:
    decision = router.route(
        SupervisorMessage(
            message_type="text",
            content="帮我查一下 EVER GIVEN 当前船位",
        )
    )

    assert decision.intent == "skill_candidate"
    assert decision.target == "skill_hub"
    assert decision.skill_candidate is not None
    assert decision.skill_candidate.skill_name == "ship.position.query"
    assert decision.skill_candidate.arguments == {"keyword": "EVER GIVEN"}
    assert decision.skill_candidate.missing_arguments == []


def test_routes_skill_candidate_without_required_keyword(router: SupervisorRouter) -> None:
    decision = router.route(
        SupervisorMessage(
            message_type="text",
            content="帮我查一下当前船位",
        )
    )

    assert decision.intent == "skill_candidate"
    assert decision.skill_candidate is not None
    assert decision.skill_candidate.skill_name == "ship.position.query"
    assert decision.skill_candidate.arguments == {}
    assert decision.skill_candidate.missing_arguments == ["keyword"]


def test_routes_handoff_requests_to_human_pending(router: SupervisorRouter) -> None:
    decision = router.route(
        SupervisorMessage(
            message_type="text",
            content="我要投诉，找人工客服。",
        )
    )

    assert decision.intent == "handoff_required"
    assert decision.target == "human_handoff_service"
    assert decision.handoff_status == "human_pending"
    assert decision.execution_mode == "route_only"


def test_routes_general_chat_as_fallback(router: SupervisorRouter) -> None:
    decision = router.route(
        SupervisorMessage(
            message_type="text",
            content="你好，今天过得怎么样？",
        )
    )

    assert decision.intent == "general_chat"
    assert decision.target == "model_gateway"
    assert decision.handoff_status == "ai_active"
    assert decision.execution_mode == "route_only"
