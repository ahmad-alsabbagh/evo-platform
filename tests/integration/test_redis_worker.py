import os

import pytest
from redis.asyncio import Redis

from evo_platform.workers.contracts import EvaluationJob
from evo_platform.workers.idempotency import RedisIdempotencyStore
from evo_platform.workers.queue import RedisStreamQueue


@pytest.fixture
async def client():
    redis_url = os.environ.get("EVO_REDIS_URL", "redis://localhost:6379/0")
    connection = Redis.from_url(redis_url)
    await connection.flushdb()
    yield connection
    await connection.flushdb()
    await connection.aclose()


@pytest.mark.integration
async def test_enqueue_read_acknowledge(client) -> None:
    queue = RedisStreamQueue(client, stream="test:evaluation", group="test-group")
    job = EvaluationJob(job_id="job-1", run_id="run-1", idempotency_key="key-1", payload={})

    await queue.enqueue(job)
    read = await queue.read("consumer-1", count=10)

    assert len(read) == 1
    message_id, decoded_job = read[0]
    assert decoded_job.job_id == "job-1"

    await queue.acknowledge(message_id)


@pytest.mark.integration
async def test_claim_stale_recovers_unacked_messages(client) -> None:
    queue = RedisStreamQueue(client, stream="test:evaluation:stale", group="test-group")
    job = EvaluationJob(job_id="job-2", run_id="run-2", idempotency_key="key-2", payload={})

    await queue.enqueue(job)
    await queue.read("consumer-a", count=10)

    claimed = await queue.claim_stale("consumer-b", min_idle_ms=0, count=10)

    assert len(claimed) == 1
    assert claimed[0][1].job_id == "job-2"


@pytest.mark.integration
async def test_move_to_dead_letter(client) -> None:
    queue = RedisStreamQueue(
        client,
        stream="test:evaluation:dlq-src",
        group="test-group",
        dead_letter_stream="test:evaluation:dlq",
    )
    job = EvaluationJob(job_id="job-3", run_id="run-3", idempotency_key="key-3", payload={})

    await queue.enqueue(job)
    read = await queue.read("consumer-1", count=10)
    message_id, decoded_job = read[0]

    await queue.move_to_dead_letter(message_id, decoded_job, reason="HANDLER_ERROR")

    dlq_messages = await client.xrange("test:evaluation:dlq")
    assert len(dlq_messages) == 1


@pytest.mark.integration
async def test_idempotency_claim_is_exclusive(client) -> None:
    store = RedisIdempotencyStore(client, prefix="test:idempotency:")

    first = await store.claim("key-4", ttl_seconds=60)
    second = await store.claim("key-4", ttl_seconds=60)

    assert first is True
    assert second is False
