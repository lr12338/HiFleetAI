from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


EXPECTED_TABLES = {
    "users",
    "conversations",
    "messages",
    "model_calls",
    "retrieval_logs",
    "skills",
    "tool_calls",
    "handoff_events",
    "conversation_notes",
    "harness_runs",
    "harness_results",
}


def build_alembic_config(sqlite_path: Path) -> Config:
    repo_root = Path(__file__).resolve().parents[2]
    config = Config(str(repo_root / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{sqlite_path}")
    return config


def test_alembic_upgrade_creates_foundational_phase_zero_tables(tmp_path: Path) -> None:
    sqlite_path = tmp_path / "phase0-migrations.db"
    config = build_alembic_config(sqlite_path)

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{sqlite_path}")
    try:
        actual_tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    assert EXPECTED_TABLES.issubset(actual_tables)
