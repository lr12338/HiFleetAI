from __future__ import annotations

from abc import ABC, abstractmethod
import json
from time import perf_counter
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

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

        payload = {
            "model": self.model_name,
            "input": _build_ark_input(request),
        }
        if request.temperature > 0:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_output_tokens"] = request.max_tokens

        http_request = urllib_request.Request(
            self._settings.ark_base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._settings.ark_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib_request.urlopen(http_request, timeout=60) as response:
                raw_body = response.read().decode("utf-8")
        except urllib_error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            parsed_error = _parse_ark_error(error_body)
            return ModelGatewayResponse.failure(
                provider=self.name,
                model_name=self.model_name,
                code=f"http_{exc.code}",
                message=parsed_error or f"Ark request failed with HTTP {exc.code}.",
                retryable=exc.code >= 500 or exc.code == 429,
                latency_ms=_latency_ms(started_at),
                request_metadata=request.metadata,
                details={
                    "base_url": self._settings.ark_base_url,
                    "http_status": exc.code,
                },
            )
        except urllib_error.URLError as exc:
            return ModelGatewayResponse.failure(
                provider=self.name,
                model_name=self.model_name,
                code="network_error",
                message=f"Ark request failed: {exc.reason}",
                retryable=True,
                latency_ms=_latency_ms(started_at),
                request_metadata=request.metadata,
                details={"base_url": self._settings.ark_base_url},
            )

        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            return ModelGatewayResponse.failure(
                provider=self.name,
                model_name=self.model_name,
                code="invalid_response",
                message="Ark returned a non-JSON response.",
                retryable=True,
                latency_ms=_latency_ms(started_at),
                request_metadata=request.metadata,
                details={"base_url": self._settings.ark_base_url},
            )

        output_text = _extract_ark_output_text(body)
        if not output_text:
            return ModelGatewayResponse.failure(
                provider=self.name,
                model_name=self.model_name,
                code="empty_response",
                message="Ark returned no text output.",
                retryable=True,
                latency_ms=_latency_ms(started_at),
                request_metadata=request.metadata,
                details={"base_url": self._settings.ark_base_url},
            )

        usage_payload = body.get("usage") if isinstance(body, dict) else None
        input_tokens = _int_from_mapping(usage_payload, "input_tokens")
        output_tokens = _int_from_mapping(usage_payload, "output_tokens")
        total_tokens = _int_from_mapping(usage_payload, "total_tokens")
        if total_tokens is None:
            total_tokens = (input_tokens or 0) + (output_tokens or 0)
        usage = ModelUsage(
            prompt_tokens=input_tokens or 0,
            completion_tokens=output_tokens or 0,
            total_tokens=total_tokens or 0,
        )
        return ModelGatewayResponse.success(
            provider=self.name,
            model_name=self.model_name,
            output_text=output_text,
            usage=usage,
            latency_ms=_latency_ms(started_at),
            request_metadata=request.metadata,
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


def _build_ark_input(request: ModelGatewayRequest) -> list[dict[str, Any]]:
    return [
        {
            "role": message.role,
            "content": [{"type": "input_text", "text": message.content}],
        }
        for message in request.messages
    ]


def _parse_ark_error(raw_body: str) -> str | None:
    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError:
        return raw_body.strip() or None

    if isinstance(body, dict):
        error_payload = body.get("error")
        if isinstance(error_payload, dict):
            message = error_payload.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
        message = body.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()
    return raw_body.strip() or None


def _extract_ark_output_text(body: object) -> str | None:
    if not isinstance(body, dict):
        return None

    output_text = body.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output_items = body.get("output")
    if isinstance(output_items, list):
        for item in output_items:
            if not isinstance(item, dict):
                continue
            content_items = item.get("content")
            if isinstance(content_items, list):
                for content_item in content_items:
                    if not isinstance(content_item, dict):
                        continue
                    text = content_item.get("text")
                    if isinstance(text, str) and text.strip():
                        return text.strip()
    return None


def _int_from_mapping(payload: object, key: str) -> int | None:
    if not isinstance(payload, dict):
        return None
    value = payload.get(key)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None
