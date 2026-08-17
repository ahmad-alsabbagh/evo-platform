from unittest.mock import AsyncMock

import pytest

from evo_platform.workers.contracts import EvaluationJob, JobStatus
from evo_platform.workers.runner import run_job


def test_job_attempt_bounds() -> None:
    with pytest.raises(ValueError):
        EvaluationJob(job_id="job", run_id="run", idempotency_key="key", attempt=11, payload={})


@pytest.mark.asyncio
async def test_idempotent_job_is_not_reexecuted() -> None:
    store = AsyncMock()
    store.claim.return_value = False
    handler = AsyncMock()
    job = EvaluationJob(job_id="job", run_id="run", idempotency_key="key", payload={})

    result = await run_job(job, handler, store)

    assert result.status == JobStatus.succeeded
    handler.assert_not_awaited()
    store.claim.assert_awaited_once()


@pytest.mark.asyncio
async def test_failed_job_is_bounded() -> None:
    store = AsyncMock()
    store.claim.return_value = True
    handler = AsyncMock(side_effect=RuntimeError("boom"))
    job = EvaluationJob(job_id="job", run_id="run", idempotency_key="key", max_attempts=1, payload={})

    result = await run_job(job, handler, store)

    assert result.status == JobStatus.dead_lettered
    assert result.attempt == 1
