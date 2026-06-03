from pathlib import Path

import pytest

from backend.app.core import config


def test_settings_defaults_are_safe_for_development() -> None:
    settings = config.get_settings(env={})

    assert settings.app_env == "development"
    assert settings.app_name == "HiFleetAI"
    assert settings.app_port == 8000
    assert settings.database_url == "postgresql+psycopg://hifleet:change-me@localhost:5432/hifleet_ai"
    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.minio_secure is False
    assert settings.ark_api_key == ""
    assert settings.harness_agent_base_url == "http://localhost:8000"


def test_settings_can_be_overridden_by_environment_values() -> None:
    settings = config.get_settings(
        env={
            "APP_ENV": "production",
            "APP_NAME": "Hifleet Test",
            "APP_PORT": "9001",
            "SECRET_KEY": "local-test-secret",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
            "DATABASE_URL": "postgresql+psycopg://user:pass@db:5432/app",
            "REDIS_URL": "redis://redis:6379/1",
            "MINIO_SECURE": "true",
            "ARK_API_KEY": "local-test-ark-key",
            "ARK_TEXT_MODEL": "test-text-model",
            "HARNESS_REPORT_DIR": "tmp/harness-reports",
        }
    )

    assert settings.app_env == "production"
    assert settings.app_name == "Hifleet Test"
    assert settings.app_port == 9001
    assert settings.secret_key == "local-test-secret"
    assert settings.access_token_expire_minutes == 15
    assert settings.database_url == "postgresql+psycopg://user:pass@db:5432/app"
    assert settings.redis_url == "redis://redis:6379/1"
    assert settings.minio_secure is True
    assert settings.ark_api_key == "local-test-ark-key"
    assert settings.ark_text_model == "test-text-model"
    assert settings.harness_report_dir == "tmp/harness-reports"


def test_production_runtime_validation_rejects_placeholder_secret() -> None:
    settings = config.get_settings(
        env={
            "APP_ENV": "production",
            "SECRET_KEY": "change-me",
        }
    )

    with pytest.raises(config.ConfigurationError, match="SECRET_KEY"):
        settings.validate_for_runtime()


def test_config_source_does_not_hardcode_real_secret_patterns() -> None:
    source = Path(config.__file__).read_text(encoding="utf-8")

    forbidden_secret_markers = [
        "-----BEGIN PRIVATE KEY-----",
        "AKIA",
        "sk-",
        "xoxb-",
        "xoxp-",
        "ghp_",
        "gho_",
    ]

    for marker in forbidden_secret_markers:
        assert marker not in source
