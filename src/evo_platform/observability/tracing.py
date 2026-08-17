from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider


def configure_tracing(service_name: str, *, engine: object | None = None) -> None:
    provider = TracerProvider(resource=Resource.create({SERVICE_NAME: service_name}))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument()
    if engine is not None:
        SQLAlchemyInstrumentor().instrument(engine=engine)
