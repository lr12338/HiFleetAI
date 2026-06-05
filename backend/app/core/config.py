"""Application configuration loaded from environment variables.

The module intentionally uses only the Python standard library so Phase 0 tasks
can run before the backend dependency stack is finalized.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping


class ConfigurationError(ValueError):
    """Raised when configuration is invalid for the requested runtime mode."""


CONFIG_ENV_VARS = (
    "APP_ENV",
    "APP_NAME",
    "APP_HOST",
    "APP_PORT",
    "SECRET_KEY",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "DATABASE_BACKEND",
    "SQLITE_DB_PATH",
    "DATABASE_URL",
    "REDIS_URL",
    "MINIO_ENDPOINT",
    "MINIO_ACCESS_KEY",
    "MINIO_SECRET_KEY",
    "MINIO_BUCKET",
    "MINIO_SECURE",
    "MODEL_PROVIDER",
    "ARK_API_KEY",
    "ARK_BASE_URL",
    "ARK_TEXT_MODEL",
    "ARK_VISION_MODEL",
    "HARNESS_AGENT_BASE_URL",
    "HARNESS_REPORT_DIR",
)

PLACEHOLDER_SECRET_VALUES = frozenset(
    {
        "",
        "change-me",
        "dev-only-change-me",
        "replace-with-your-local-key",
    }
)


@dataclass(frozen=True)
class Settings:
    app_env: str
    app_name: str
    app_host: str
    app_port: int
    secret_key: str
    access_token_expire_minutes: int
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    database_backend: str
    sqlite_db_path: str
    database_url: str
    redis_url: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str
    minio_secure: bool
    model_provider: str
    ark_api_key: str
    ark_base_url: str
    ark_text_model: str
    ark_vision_model: str
    harness_agent_base_url: str
    harness_report_dir: str

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    def validate_for_runtime(self) -> None:
        """Validate settings that are unsafe to leave as placeholders."""
        if not self.is_production:
            return

        if self.secret_key in PLACEHOLDER_SECRET_VALUES:
            raise ConfigurationError("SECRET_KEY must be set for production runtime")


def get_settings(
    *,
    env: Mapping[str, str] | None = None,
    env_file: str | Path | None = None,
) -> Settings:
    """Build a Settings object from an env file and process environment values."""
    source_env = dict(os.environ if env is None else env)
    if env_file is not None:
        file_env = load_env_file(env_file)
        source_env = {**file_env, **source_env}

    postgres_host = _read(source_env, "POSTGRES_HOST", "localhost")
    postgres_port = _read_int(source_env, "POSTGRES_PORT", 5432)
    postgres_db = _read(source_env, "POSTGRES_DB", "hifleet_ai")
    postgres_user = _read(source_env, "POSTGRES_USER", "hifleet")
    postgres_password = _read(source_env, "POSTGRES_PASSWORD", "change-me")
    database_backend = _read(source_env, "DATABASE_BACKEND", "sqlite").lower()
    sqlite_db_path = _read(source_env, "SQLITE_DB_PATH", "data/app-dev.db")
    database_url = _resolve_database_url(
        env=source_env,
        database_backend=database_backend,
        sqlite_db_path=sqlite_db_path,
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        postgres_db=postgres_db,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
    )

    return Settings(
        app_env=_read(source_env, "APP_ENV", "development"),
        app_name=_read(source_env, "APP_NAME", "HiFleetAI"),
        app_host=_read(source_env, "APP_HOST", "0.0.0.0"),
        app_port=_read_int(source_env, "APP_PORT", 8000),
        secret_key=_read(source_env, "SECRET_KEY", "dev-only-change-me"),
        access_token_expire_minutes=_read_int(source_env, "ACCESS_TOKEN_EXPIRE_MINUTES", 60),
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        postgres_db=postgres_db,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
        database_backend=database_backend,
        sqlite_db_path=sqlite_db_path,
        database_url=database_url,
        redis_url=_read(source_env, "REDIS_URL", "redis://localhost:6379/0"),
        minio_endpoint=_read(source_env, "MINIO_ENDPOINT", "localhost:9000"),
        minio_access_key=_read(source_env, "MINIO_ACCESS_KEY", "change-me"),
        minio_secret_key=_read(source_env, "MINIO_SECRET_KEY", "change-me"),
        minio_bucket=_read(source_env, "MINIO_BUCKET", "hifleet-ai"),
        minio_secure=_read_bool(source_env, "MINIO_SECURE", False),
        model_provider=_read(source_env, "MODEL_PROVIDER", "ark"),
        ark_api_key=_read(source_env, "ARK_API_KEY", ""),
        ark_base_url=_read(
            source_env,
            "ARK_BASE_URL",
            "https://ark.cn-beijing.volces.com/api/v3/responses",
        ),
        ark_text_model=_read(source_env, "ARK_TEXT_MODEL", "deepseek-v4-flash-260425"),
        ark_vision_model=_read(source_env, "ARK_VISION_MODEL", "doubao-seed-2-0-lite-260215"),
        harness_agent_base_url=_read(
            source_env,
            "HARNESS_AGENT_BASE_URL",
            "http://localhost:8000",
        ),
        harness_report_dir=_read(source_env, "HARNESS_REPORT_DIR", "harness/reports"),
    )


def load_env_file(path: str | Path) -> dict[str, str]:
    """Load a simple KEY=VALUE env file without mutating os.environ."""
    env_path = Path(path)
    if not env_path.exists():
        raise ConfigurationError(f"Environment file not found: {env_path}")

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(env_path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigurationError(f"Invalid env line {line_number}: missing '='")

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise ConfigurationError(f"Invalid env line {line_number}: empty key")
        values[key] = _strip_optional_quotes(value.strip())
    return values


def _build_database_url(*, user: str, password: str, host: str, port: int, database: str) -> str:
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"


def _build_sqlite_url(path: str | Path) -> str:
    return f"sqlite:///{Path(path).resolve()}"


def _resolve_database_url(
    *,
    env: Mapping[str, str],
    database_backend: str,
    sqlite_db_path: str,
    postgres_host: str,
    postgres_port: int,
    postgres_db: str,
    postgres_user: str,
    postgres_password: str,
) -> str:
    explicit_database_url = env.get("DATABASE_URL")
    if explicit_database_url:
        return explicit_database_url

    if database_backend == "sqlite":
        return _build_sqlite_url(sqlite_db_path)
    if database_backend == "postgres":
        return _build_database_url(
            user=postgres_user,
            password=postgres_password,
            host=postgres_host,
            port=postgres_port,
            database=postgres_db,
        )
    raise ConfigurationError("DATABASE_BACKEND must be either 'sqlite' or 'postgres'")


def _read(env: Mapping[str, str], key: str, default: str) -> str:
    value = env.get(key)
    if value is None or value == "":
        return default
    return value


def _read_int(env: Mapping[str, str], key: str, default: int) -> int:
    value = _read(env, key, str(default))
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigurationError(f"{key} must be an integer") from exc


def _read_bool(env: Mapping[str, str], key: str, default: bool) -> bool:
    value = _read(env, key, str(default)).lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(f"{key} must be a boolean")


def _strip_optional_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
