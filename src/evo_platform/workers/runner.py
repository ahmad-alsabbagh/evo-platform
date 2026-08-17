from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import structlog

from evo_platform.workers.contracts import EvaluationJob, JobResult, JobStatus


log = structlog.get_logger(__name__)


class IdempotencyStore(Protocol):
    async def claim(self, key: str, ttl_seconds: int) -> bool: ...
    async def release(self, key: str) -> None: ...
    async def complete(self, key: str, ttl_seconds: int) -> None: ...


async def run_job(
    job: EvaluationJob,
    handler: Callable[[EvaluationJob], Awaitable[dict[str, Any]]],
    idempotency: IdempotencyStore,
    *,
    idempotency_ttl_seconds: int = 86_400,
) -> JobResult:
    claimed = await idempotency.claim(job.idempotency_key, idempotency_ttl_seconds)
    if not claimed:
        return JobResult(job_id=job.job_id, run_id=job.run_id, status=JobStatus.succeeded, attempt=job.attempt)
    try:
        await handler(job)
        await idempotency.complete(job.idempotency_key, idempotency_ttl_seconds)
        log.info("evaluation_job_succeeded", job_id=job.job_id, run_id=job.run_id, attempt=job.attempt)
        return JobResult(job_id=job.job_id, run_id=job.run_id, status=JobStatus.succeeded, attempt=job.attempt)
    except Exception:
        await idempotency.release(job.idempotency_key)
        next_attempt = job.attempt + 1
        status = JobStatus.failed if next_attempt < job.max_attempts else JobStatus.dead_lettered
        log.exception("evaluation_job_failed", job_id=job.job_id, run_id=job.run_id, attempt=next_attempt)
        return JobResult(job_id=job.job_id, run_id=job.run_id, status=status, attempt=next_attempt, error_code="HANDLER_ERROR")
