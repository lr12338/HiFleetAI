from __future__ import annotations

from abc import ABC, abstractmethod
from time import perf_counter

from backend.app.core.config import Settings, get_settings
from backend.app.schemas.model import ModelGatewayRequest, ModelGatewayResponse, ModelUsage


class ModelProvider(ABC):
    name: str
    model_name: str

    @abstractmethod
    def generate(self, request: ModelGatewayRequest) -> ModelGatewayResponse:
        """Generate a structured response for the given request."""


class FakeModelProvider(ModelProvider):
    name = "fake"
    model_name = "fake-local-model"

    def generate(self, request: ModelGatewayRequest) -> ModelGatewayResponse:
        started_at = perf_counter()
        prompt = _last_user_message(request)
        output_text = f"Fake response: {prompt}"
        usage = ModelUsage(
            prompt_tokens=max(1, len(prompt.split())),
            completion_tokens=max(1, len(output_text.split())),
            total_tokens=max(1, len(prompt.split())) + max(1, len(output_text.split())),
        )
        return ModelGatewayResponse.success(
            provider=self.name,
            model_name=self.model_name,
            output_text=output_text,
            usage=usage,
            latency_ms=_latency_ms(started_at),
            request_metadata=request.metadata,
        )


class ArkModelProvider(ModelProvider):
    name = "ark"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.model_name = settings.ark_text_model

    def generate(self, request: ModelGatewayRequest) -> ModelGatewayResponse:
        started_at = perf_counter()
        if not self._settings.ark_api_key.strip():
            return ModelGatewayResponse.failure(
                provider=self.name,
                model_name=self.model_name,
                code="missing_credentials",
                message="ARK_API_KEY is required for the ark model provider.",
                retryable=False,
                latency_ms=_latency_ms(started_at),
                request_metadata=request.metadata,
                details={"base_url": self._settings.ark_base_url},
            )

        return ModelGatewayResponse.failure(
            provider=self.name,
            model_name=self.model_name,
            code="provider_not_enabled",
            message="Live Ark model calls are disabled in this task scope.",
            retryable=False,
            latency_ms=_latency_ms(started_at),
            request_metadata=request.metadata,
            details={"base_url": self._settings.ark_base_url},
        )


class UnsupportedModelProvider(ModelProvider):
    def __init__(self, provider_name: str) -> None:
        self.name = provider_name
        self.model_name = "unconfigured-model"

    def generate(self, request: ModelGatewayRequest) -> ModelGatewayResponse:
        started_at = perf_counter()
        return ModelGatewayResponse.failure(
            provider=self.name,
            model_name=self.model_name,
            code="unsupported_provider",
            message=f"Model provider '{self.name}' is not supported.",
            retryable=False,
            latency_ms=_latency_ms(started_at),
            request_metadata=request.metadata,
        )


class ModelGateway:
    def __init__(self, provider: ModelProvider) -> None:
        self._provider = provider

    @classmethod
    def from_settings(cls, *, settings: Settings | None = None) -> "ModelGateway":
        resolved_settings = get_settings() if settings is None else settings
        provider_name = resolved_settings.model_provider.strip().lower()
        provider = _build_provider(provider_name=provider_name, settings=resolved_settings)
        return cls(provider=provider)

    @property
    def provider_name(self) -> str:
        return self._provider.name

    def generate(self, request: ModelGatewayRequest) -> ModelGatewayResponse:
        return self._provider.generate(request)


def _build_provider(*, provider_name: str, settings: Settings) -> ModelProvider:
    if provider_name == "fake":
        return FakeModelProvider()
    if provider_name == "ark":
        return ArkModelProvider(settings=settings)
    return UnsupportedModelProvider(provider_name=provider_name or "unknown")


def _last_user_message(request: ModelGatewayRequest) -> str:
    for message in reversed(request.messages):
        if message.role == "user":
            return message.content
    return ""


def _latency_ms(started_at: float) -> int:
    return max(0, int((perf_counter() - started_at) * 1000))
