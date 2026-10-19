from unittest.mock import AsyncMock

import pytest

from evo_platform.workers.contracts import EvaluationJob
from evo_platform.workers.queue import RedisStreamQueue


@pytest.fixture
def job() -> EvaluationJob:
    return EvaluationJob(job_id="job", run_id="run", idempotency_key="key", payload={})


@pytest.mark.asyncio
async def test_enqueue_serializes_job(job: EvaluationJob) -> None:
    client = AsyncMock()
    client.xadd.return_value = "1-0"
    queue = RedisStreamQueue(client)

    result = await queue.enqueue(job)

    assert result == "1-0"
    client.xadd.assert_awaited_once()


@pytest.mark.asyncio
async def test_acknowledge_uses_consumer_group() -> None:
    client = AsyncMock()
    queue = RedisStreamQueue(client)

    await queue.acknowledge("1-0")

    client.xack.assert_awaited_once_with("evo:evaluation", "evo-workers", "1-0")
