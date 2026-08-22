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

## Catalog boundary

Catalog entries are discovery metadata, not proof of quality. Promotion requires a linked evaluation run, provenance, license metadata, and policy checks. Collections are versioned and owned; their items reference stable capability IDs and versions.

## Worker boundary

HTTP handlers enqueue evaluation jobs and return a run identifier. Workers consume jobs through a Redis Streams consumer group with at-least-once delivery. Unacknowledged messages are recovered through `XAUTOCLAIM` after a visibility timeout. Idempotency uses an atomic claim (`SETNX` with TTL) before executing a handler, and the claim is marked complete only after success. Jobs that exhaust retries are moved to a dedicated dead-letter stream with the failure reason and original message id.

## Observability

Every request receives a correlation ID. Traces cover HTTP and database boundaries, while structured JSON logs carry request and trace context. Logs must redact credentials, tokens, prompts containing sensitive data, and raw model outputs by default.
