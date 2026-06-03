from __future__ import annotations

import re

from backend.app.schemas.supervisor import (
    SkillCandidatePlan,
    SupervisorDecision,
    SupervisorMessage,
)


class SupervisorRouter:
    """Deterministic, rule-first router for MVP supervisor decisions."""

    def route(self, message: SupervisorMessage) -> SupervisorDecision:
        text = _normalize_text(message.content)

        if _needs_handoff(text):
            return SupervisorDecision(
                intent="handoff_required",
                target="human_handoff_service",
                reason="Detected an explicit handoff or complaint request.",
                handoff_status="human_pending",
                metadata={"policy": "rule_first", "matched_rule": "handoff_request"},
            )

        if message.has_image_input():
            return SupervisorDecision(
                intent="image_understanding",
                target="multimodal_processor",
                reason="Detected image input from the message type or attachment list.",
                handoff_status="ai_active",
                metadata={"policy": "rule_first", "matched_rule": "image_input"},
            )

        if _is_skill_candidate(text):
            skill_candidate = _build_skill_candidate(text)
            return SupervisorDecision(
                intent="skill_candidate",
                target="skill_hub",
                reason="Detected an operational query that matches a known MVP skill pattern.",
                handoff_status="ai_active",
                skill_candidate=skill_candidate,
                metadata={"policy": "rule_first", "matched_rule": "skill_candidate"},
            )

        if _needs_web_research(text):
            return SupervisorDecision(
                intent="web_research",
                target="deep_search_hub",
                reason="Detected a request for recent or public information with source expectations.",
                handoff_status="ai_active",
                requires_sources=True,
                metadata={"policy": "rule_first", "matched_rule": "web_research"},
            )

        if _is_faq(text):
            return SupervisorDecision(
                intent="faq",
                target="knowledge_hub",
                reason="Detected a product or usage question suited for internal knowledge answers.",
                handoff_status="ai_active",
                metadata={"policy": "rule_first", "matched_rule": "faq_query"},
            )

        return SupervisorDecision(
            intent="general_chat",
            target="model_gateway",
            reason="No higher-priority routing rule matched the request.",
            handoff_status="ai_active",
            metadata={"policy": "rule_first", "matched_rule": "general_chat_fallback"},
        )


def _normalize_text(content: str) -> str:
    return re.sub(r"\s+", " ", content).strip()


def _needs_handoff(text: str) -> bool:
    handoff_keywords = (
        "人工客服",
        "转人工",
        "找人工",
        "人工处理",
        "人工介入",
        "联系人工",
        "投诉",
        "升级处理",
    )
    return any(keyword in text for keyword in handoff_keywords)


def _is_skill_candidate(text: str) -> bool:
    if _is_faq(text):
        return False

    action_keywords = ("帮我查", "查一下", "查下", "查询", "查查", "帮我看", "看下")
    skill_topics = ("船位", "位置", "船舶档案", "船舶资料", "港口船舶", "区域船舶", "统计")
    return any(keyword in text for keyword in action_keywords) and any(
        topic in text for topic in skill_topics
    )


def _build_skill_candidate(text: str) -> SkillCandidatePlan:
    if "船位" in text or "位置" in text:
        keyword = _extract_ship_keyword(text)
        if keyword:
            return SkillCandidatePlan(
                skill_name="ship.position.query",
                arguments={"keyword": keyword},
            )
        return SkillCandidatePlan(
            skill_name="ship.position.query",
            arguments={},
            missing_arguments=["keyword"],
        )

    if "档案" in text or "资料" in text:
        keyword = _extract_ship_keyword(text)
        if keyword:
            return SkillCandidatePlan(
                skill_name="ship.profile.query",
                arguments={"keyword": keyword},
            )
        return SkillCandidatePlan(
            skill_name="ship.profile.query",
            arguments={},
            missing_arguments=["keyword"],
        )

    if "港口" in text and "统计" in text:
        return SkillCandidatePlan(skill_name="port.vessel.count")

    return SkillCandidatePlan(skill_name="area.vessel.statistics")


def _extract_ship_keyword(text: str) -> str | None:
    patterns = (
        r"(?:帮我查|查一下|查下|查询)\s*([A-Za-z0-9][A-Za-z0-9\s\-]{2,})\s*(?:当前)?(?:船位|位置)",
        r"\b([A-Z0-9][A-Z0-9\s\-]{2,})\b(?=\s*(?:当前)?(?:船位|位置))",
        r"[\"“](.+?)[\"”](?=\s*(?:当前)?(?:船位|位置))",
    )

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            candidate = re.sub(r"\s+", " ", match.group(1)).strip(" -")
            if candidate:
                return candidate
    return None


def _needs_web_research(text: str) -> bool:
    direct_research_keywords = ("检索", "搜索", "搜一下", "查新闻", "网页", "网址", "来源")
    freshness_keywords = ("近期", "最近", "最新", "公开", "新闻", "政策")
    return any(keyword in text for keyword in direct_research_keywords) or (
        any(keyword in text for keyword in freshness_keywords) and "来源" in text
    )


def _is_faq(text: str) -> bool:
    question_keywords = ("怎么", "如何", "步骤", "使用", "开通", "登录", "介绍", "说明")
    product_keywords = ("Hifleet", "平台", "系统", "功能", "船位")
    return any(keyword in text for keyword in question_keywords) and any(
        keyword in text for keyword in product_keywords
    )
