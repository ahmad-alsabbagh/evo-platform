from unittest.mock import AsyncMock

import pytest

from evo_platform.workers.contracts import EvaluationJob, JobStatus
from evo_platform.workers.runner import run_job


@pytest.mark.asyncio
async def test_failed_job_releases_claim_for_retry() -> None:
    store = AsyncMock()
    store.claim.return_value = True
    handler = AsyncMock(side_effect=RuntimeError("boom"))
    job = EvaluationJob(
        job_id="job", run_id="run", idempotency_key="key", max_attempts=2, payload={}
    )
    result = await run_job(job, handler, store)
    assert result.status == JobStatus.failed
    store.release.assert_awaited_once_with("key")
