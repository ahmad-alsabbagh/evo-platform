from collections.abc import Sequence
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SpanExportResult,
    SpanExporter,
    SpanProcessor,
)


_instrumented_fastapi = False
_instrumented_engines: set[int] = set()


class _NoopExporter(SpanExporter):
    def export(self, spans: Sequence[Any]) -> SpanExportResult:
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        return None


def configure_tracing(
    service_name: str,
    *,
    endpoint: str | None = None,
    sample_ratio: float = 1.0,
    engine: object | None = None,
) -> None:
    global _instrumented_fastapi
    provider = TracerProvider(resource=Resource.create({SERVICE_NAME: service_name}))
    if endpoint:
        exporter: SpanExporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    else:
        exporter = _NoopExporter()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    if not _instrumented_fastapi:
        FastAPIInstrumentor.instrument()
        _instrumented_fastapi = True
    if engine is not None and id(engine) not in _instrumented_engines:
        SQLAlchemyInstrumentor().instrument(engine=engine)
        _instrumented_engines.add(id(engine))
