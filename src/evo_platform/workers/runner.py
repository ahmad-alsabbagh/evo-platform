from collections.abc import Awaitable, Callable
from typing import Any

import structlog

from evo_platform.workers.contracts import EvaluationJob, JobResult, JobStatus


log = structlog.get_logger(__name__)


class IdempotencyStore:
    async def seen(self, key: str) -> bool:
        raise NotImplementedError

    async def mark(self, key: str) -> None:
        raise NotImplementedError


async def run_job(
    job: EvaluationJob,
    handler: Callable[[EvaluationJob], Awaitable[dict[str, Any]]],
    idempotency: IdempotencyStore,
) -> JobResult:
    if await idempotency.seen(job.idempotency_key):
        return JobResult(job_id=job.job_id, run_id=job.run_id, status=JobStatus.succeeded, attempt=job.attempt)
    try:
        await idempotency.mark(job.idempotency_key)
        await handler(job)
        log.info("evaluation_job_succeeded", job_id=job.job_id, run_id=job.run_id, attempt=job.attempt)
        return JobResult(job_id=job.job_id, run_id=job.run_id, status=JobStatus.succeeded, attempt=job.attempt)
    except Exception:
        next_attempt = job.attempt + 1
        status = JobStatus.failed if next_attempt < job.max_attempts else JobStatus.dead_lettered
        log.exception("evaluation_job_failed", job_id=job.job_id, run_id=job.run_id, attempt=next_attempt)
        return JobResult(job_id=job.job_id, run_id=job.run_id, status=status, attempt=next_attempt, error_code="HANDLER_ERROR")
