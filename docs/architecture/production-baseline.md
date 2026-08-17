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

## Next milestones

1. Add common schema definitions and contract fixtures.
2. Add repository and transaction boundaries.
3. Add queue-backed evaluation workers with idempotency.
4. Add OpenTelemetry exporters and structured audit events.
5. Add regression and promotion policies.
