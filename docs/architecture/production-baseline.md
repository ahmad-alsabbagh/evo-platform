# Production Engineering Baseline

## Scope

EvoPlatform starts as a modular monolith with a strict boundary between API request handling and long-running evaluation workers.

## Principles

- Contracts are versioned and validated at runtime and in CI.
- Evaluation runs are reproducible and immutable after completion.
- External model and tool calls are observable, bounded by timeouts, and budgeted.
- Side effects require explicit policy authorization.
- Evidence and audit records are retained independently from request logs.
- Database changes are applied only through reviewed, forward-compatible migrations.

## Persistence boundary

PostgreSQL stores indexed evaluation metadata and the canonical JSON payload. Large artifacts, traces, and reports belong in object storage and are referenced by immutable digest.

## Observability

Every request receives a correlation ID. Traces cover HTTP and database boundaries, while structured JSON logs carry request and trace context. Logs must redact credentials, tokens, prompts containing sensitive data, and raw model outputs by default.

## Next milestones

1. Add repository and transaction boundaries.
2. Add queue-backed evaluation workers with idempotency.
3. Add OpenTelemetry exporters and structured audit events.
4. Add regression and promotion policies.
