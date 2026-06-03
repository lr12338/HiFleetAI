from __future__ import annotations

from backend.app.agent.model_gateway import ModelGateway
from backend.app.core.config import get_settings
from backend.app.schemas.model import ModelGatewayRequest, ModelMessage


def build_request() -> ModelGatewayRequest:
    return ModelGatewayRequest(
        messages=[
            ModelMessage(role="system", content="You are a helpful assistant."),
            ModelMessage(role="user", content="你好，请介绍一下模型网关。"),
        ],
        metadata={"trace_id": "test-trace"},
    )


def test_gateway_selects_provider_from_settings() -> None:
    settings = get_settings(
        env={
            "MODEL_PROVIDER": "fake",
        }
    )

    gateway = ModelGateway.from_settings(settings=settings)

    assert gateway.provider_name == "fake"


def test_fake_provider_returns_structured_success() -> None:
    settings = get_settings(
        env={
            "MODEL_PROVIDER": "fake",
        }
    )
    gateway = ModelGateway.from_settings(settings=settings)

    response = gateway.generate(build_request())

    assert response.status == "success"
    assert response.provider == "fake"
    assert response.model_name == "fake-local-model"
    assert response.output_text == "Fake response: 你好，请介绍一下模型网关。"
    assert response.error is None
    assert response.usage is not None
    assert response.usage.prompt_tokens > 0
    assert response.usage.completion_tokens > 0


def test_missing_credentials_returns_structured_failure() -> None:
    settings = get_settings(
        env={
            "MODEL_PROVIDER": "ark",
            "ARK_API_KEY": "",
            "ARK_TEXT_MODEL": "deepseek-v4-flash-260425",
        }
    )
    gateway = ModelGateway.from_settings(settings=settings)

    response = gateway.generate(build_request())

    assert response.status == "error"
    assert response.provider == "ark"
    assert response.model_name == "deepseek-v4-flash-260425"
    assert response.output_text is None
    assert response.error is not None
    assert response.error.code == "missing_credentials"
    assert response.error.retryable is False
    assert "ARK_API_KEY" in response.error.message
