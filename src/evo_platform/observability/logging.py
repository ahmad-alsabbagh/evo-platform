import logging
import sys
from collections.abc import Mapping
from typing import Any

import structlog
from opentelemetry import trace

SENSITIVE_KEYS = frozenset({"password", "token", "secret", "authorization", "api_key", "apikey", "prompt", "output", "content"})


def redact_sensitive(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    def scrub(value: Any, key: str | None = None) -> Any:
        if key and key.lower() in SENSITIVE_KEYS:
            return "[REDACTED]"
        if isinstance(value, Mapping):
            return {str(k): scrub(v, str(k)) for k, v in value.items()}
        if isinstance(value, list):
            return [scrub(item) for item in value]
        if isinstance(value, tuple):
            return tuple(scrub(item) for item in value)
        return value

    return scrub(event_dict)


def add_trace_context(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    context = trace.get_current_span().get_span_context()
    if context.is_valid:
        event_dict["trace_id"] = format(context.trace_id, "032x")
        event_dict["span_id"] = format(context.span_id, "016x")
    return event_dict


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            redact_sensitive,
            add_trace_context,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s", force=True)
