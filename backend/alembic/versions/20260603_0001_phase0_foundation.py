"""Create foundational Phase 0 tables.

Revision ID: 20260603_0001
Revises:
Create Date: 2026-06-03 20:05:00+08:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260603_0001"
down_revision = None
branch_labels = None
depends_on = None


UUID_STR = sa.Uuid(as_uuid=False)
TIMESTAMP_TZ = sa.DateTime(timezone=True)
JSON_TYPE = sa.JSON()


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID_STR, primary_key=True, nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("user_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("metadata", JSON_TYPE, nullable=True),
        sa.Column("created_at", TIMESTAMP_TZ, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TIMESTAMP_TZ, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "conversations",
        sa.Column("id", UUID_STR, primary_key=True, nullable=False),
        sa.Column("user_id", UUID_STR, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("channel_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("handoff_status", sa.String(length=50), nullable=False),
        sa.Column("assigned_agent_id", UUID_STR, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("last_message_at", TIMESTAMP_TZ, nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("metadata", JSON_TYPE, nullable=True),
        sa.Column("created_at", TIMESTAMP_TZ, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TIMESTAMP_TZ, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "messages",
        sa.Column("id", UUID_STR, primary_key=True, nullable=False),
        sa.Column("conversation_id", UUID_STR, sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("sender_type", sa.String(length=50), nullable=False),
        sa.Column("sender_id", UUID_STR, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("message_type", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("content_payload", JSON_TYPE, nullable=True),
        sa.Column("channel_message_id", sa.String(length=255), nullable=True),
        sa.Column("send_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", TIMESTAMP_TZ, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "model_calls",
        sa.Column("id", UUID_STR, primary_key=True, nullable=False),
        sa.Column("conversation_id", UUID_STR, sa.ForeignKey("conversations.id"), nullable=True),
        sa.Column("message_id", UUID_STR, sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", TIMESTAMP_TZ, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "retrieval_logs",
        sa.Column("id", UUID_STR, primary_key=True, nullable=False),
        sa.Column("conversation_id", UUID_STR, sa.ForeignKey("conversations.id"), nullable=True),
        sa.Column("message_id", UUID_STR, sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("retrieval_type", sa.String(length=50), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("results", JSON_TYPE, nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", TIMESTAMP_TZ, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "skills",
        sa.Column("id", UUID_STR, primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("input_schema", JSON_TYPE, nullable=True),
        sa.Column("output_schema", JSON_TYPE, nullable=True),
        sa.Column("permission_level", sa.String(length=50), nullable=False),
        sa.Column("execution_mode", sa.String(length=50), nullable=False),
        sa.Column("config", JSON_TYPE, nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", TIMESTAMP_TZ, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TIMESTAMP_TZ, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("name", name="uq_skills_name"),
    )

    op.create_table(
        "tool_calls",
        sa.Column("id", UUID_STR, primary_key=True, nullable=False),
        sa.Column("conversation_id", UUID_STR, sa.ForeignKey("conversations.id"), nullable=True),
        sa.Column("message_id", UUID_STR, sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("skill_id", UUID_STR, sa.ForeignKey("skills.id"), nullable=True),
        sa.Column("tool_name", sa.String(length=255), nullable=False),
        sa.Column("input_payload", JSON_TYPE, nullable=True),
        sa.Column("output_payload", JSON_TYPE, nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", TIMESTAMP_TZ, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "handoff_events",
        sa.Column("id", UUID_STR, primary_key=True, nullable=False),
        sa.Column("conversation_id", UUID_STR, sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("operator_id", UUID_STR, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata", JSON_TYPE, nullable=True),
        sa.Column("created_at", TIMESTAMP_TZ, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "conversation_notes",
        sa.Column("id", UUID_STR, primary_key=True, nullable=False),
        sa.Column("conversation_id", UUID_STR, sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("author_id", UUID_STR, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", TIMESTAMP_TZ, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "harness_runs",
        sa.Column("id", UUID_STR, primary_key=True, nullable=False),
        sa.Column("run_name", sa.String(length=255), nullable=False),
        sa.Column("model_config", JSON_TYPE, nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("summary", JSON_TYPE, nullable=True),
        sa.Column("created_at", TIMESTAMP_TZ, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("finished_at", TIMESTAMP_TZ, nullable=True),
    )

    op.create_table(
        "harness_results",
        sa.Column("id", UUID_STR, primary_key=True, nullable=False),
        sa.Column("run_id", UUID_STR, sa.ForeignKey("harness_runs.id"), nullable=False),
        sa.Column("case_id", UUID_STR, nullable=True),
        sa.Column("actual_output", JSON_TYPE, nullable=True),
        sa.Column("score", sa.Numeric(10, 4), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", TIMESTAMP_TZ, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    op.drop_table("harness_results")
    op.drop_table("harness_runs")
    op.drop_table("conversation_notes")
    op.drop_table("handoff_events")
    op.drop_table("tool_calls")
    op.drop_table("skills")
    op.drop_table("retrieval_logs")
    op.drop_table("model_calls")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("users")
