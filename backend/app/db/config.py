from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from backend.app.core.config import get_settings


DEFAULT_RUNTIME_SQLITE_PATH = Path("data/app-dev.db")


def build_sqlite_url(path: str | Path) -> str:
    return f"sqlite:///{Path(path).resolve()}"


def get_runtime_database_url(env: Mapping[str, str] | None = None) -> str:
    """Return the runtime database URL using the shared application config."""
    return get_settings(env=os.environ if env is None else env).database_url


def get_migration_database_url(
    env: Mapping[str, str] | None = None,
    *,
    fallback_path: str | Path = DEFAULT_RUNTIME_SQLITE_PATH,
) -> str:
    """Resolve the Alembic database URL.

    Migrations should follow the same runtime backend decision as the app. An
    explicit `DATABASE_URL` always wins; otherwise local development defaults to
    the shared SQLite file and explicit PostgreSQL mode uses the composed URL.
    """
    source_env = os.environ if env is None else env
    explicit_url = source_env.get("DATABASE_URL")
    if explicit_url:
        return explicit_url

    settings = get_settings(env=source_env)
    if settings.database_backend == "postgres":
        return settings.database_url

    sqlite_path = settings.sqlite_db_path or str(fallback_path)
    return build_sqlite_url(sqlite_path)
