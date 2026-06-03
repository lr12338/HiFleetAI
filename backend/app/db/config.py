from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from backend.app.core.config import get_settings


DEFAULT_MIGRATION_SQLITE_PATH = Path("data/alembic-dev.db")


def build_sqlite_url(path: str | Path) -> str:
    return f"sqlite:///{Path(path).resolve()}"


def get_runtime_database_url(env: Mapping[str, str] | None = None) -> str:
    """Return the runtime database URL using the shared application config."""
    return get_settings(env=os.environ if env is None else env).database_url


def get_migration_database_url(
    env: Mapping[str, str] | None = None,
    *,
    fallback_path: str | Path = DEFAULT_MIGRATION_SQLITE_PATH,
) -> str:
    """Resolve the Alembic database URL.

    `alembic upgrade head` should stay executable even when PostgreSQL is not
    running locally, so migrations fall back to a repo-local SQLite file unless
    `DATABASE_URL` is provided explicitly.
    """
    source_env = os.environ if env is None else env
    explicit_url = source_env.get("DATABASE_URL")
    if explicit_url:
        return explicit_url
    return build_sqlite_url(fallback_path)
