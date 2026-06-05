from __future__ import annotations

from urllib import request as urllib_request

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


def test_ark_provider_returns_structured_success(monkeypatch) -> None:
    class FakeHttpResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self) -> bytes:
            return (
                b'{"output":[{"type":"message","content":[{"type":"output_text","text":"'
                b'\xe7\x81\xab\xe5\xb1\xb1\xe7\x9c\x9f\xe5\xae\x9e\xe8\xb0\x83\xe7\x94\xa8'
                b'"}]}],"usage":{"input_tokens":12,"output_tokens":20,"total_tokens":32}}'
            )

    captured: dict[str, object] = {}

    def fake_urlopen(http_request: urllib_request.Request, timeout: int):
        captured["url"] = http_request.full_url
        captured["authorization"] = http_request.get_header("Authorization")
        captured["headers"] = dict(http_request.header_items())
        captured["timeout"] = timeout
        captured["body"] = http_request.data
        return FakeHttpResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    settings = get_settings(
        env={
            "MODEL_PROVIDER": "ark",
            "ARK_API_KEY": "test-ark-key",
            "ARK_BASE_URL": "https://ark.cn-beijing.volces.com/api/v3/responses",
            "ARK_TEXT_MODEL": "deepseek-v4-flash-260425",
        }
    )
    gateway = ModelGateway.from_settings(settings=settings)

    response = gateway.generate(build_request())

    assert response.status == "success"
    assert response.provider == "ark"
    assert response.model_name == "deepseek-v4-flash-260425"
    assert response.output_text == "火山真实调用"
    assert response.usage is not None
    assert response.usage.prompt_tokens == 12
    assert response.usage.completion_tokens == 20
    assert response.usage.total_tokens == 32
    assert captured["url"] == "https://ark.cn-beijing.volces.com/api/v3/responses"
    assert captured["authorization"] == "Bearer test-ark-key"
    assert captured["headers"] == {
        "Authorization": "Bearer test-ark-key",
        "Content-type": "application/json",
    }
    assert captured["timeout"] == 60
