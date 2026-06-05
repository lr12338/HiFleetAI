from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


GatewayStatus = Literal["success", "error"]
MessageRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ModelMessage:
    role: MessageRole
    content: str


@dataclass(frozen=True)
class ModelGatewayRequest:
    messages: list[ModelMessage]
    temperature: float = 0.0
    max_tokens: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class ModelGatewayError:
    code: str
    message: str
    retryable: bool
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelCallLog:
    provider: str
    model_name: str
    status: GatewayStatus
    latency_ms: int
    request_metadata: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class ModelGatewayResponse:
    status: GatewayStatus
    provider: str
    model_name: str
    output_text: str | None
    usage: ModelUsage | None
    error: ModelGatewayError | None
    latency_ms: int
    log_entry: ModelCallLog

    @classmethod
    def success(
        cls,
        *,
        provider: str,
        model_name: str,
        output_text: str,
        usage: ModelUsage,
        latency_ms: int,
        request_metadata: dict[str, Any] | None = None,
    ) -> "ModelGatewayResponse":
        metadata = {} if request_metadata is None else dict(request_metadata)
        return cls(
            status="success",
            provider=provider,
            model_name=model_name,
            output_text=output_text,
            usage=usage,
            error=None,
            latency_ms=latency_ms,
            log_entry=ModelCallLog(
                provider=provider,
                model_name=model_name,
                status="success",
                latency_ms=latency_ms,
                request_metadata=metadata,
            ),
        )

    @classmethod
    def failure(
        cls,
        *,
        provider: str,
        model_name: str,
        code: str,
        message: str,
        retryable: bool,
        latency_ms: int,
        request_metadata: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> "ModelGatewayResponse":
        metadata = {} if request_metadata is None else dict(request_metadata)
        error_details = {} if details is None else dict(details)
        error = ModelGatewayError(
            code=code,
            message=message,
            retryable=retryable,
            details=error_details,
        )
        return cls(
            status="error",
            provider=provider,
            model_name=model_name,
            output_text=None,
            usage=None,
            error=error,
            latency_ms=latency_ms,
            log_entry=ModelCallLog(
                provider=provider,
                model_name=model_name,
                status="error",
                latency_ms=latency_ms,
                request_metadata=metadata,
                error_code=code,
                error_message=message,
            ),
        )
