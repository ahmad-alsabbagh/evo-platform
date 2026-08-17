from typing import Protocol

from redis.asyncio import Redis

from evo_platform.workers.contracts import EvaluationJob


class JobQueue(Protocol):
    async def enqueue(self, job: EvaluationJob) -> str: ...
    async def acknowledge(self, message_id: str) -> None: ...


class RedisStreamQueue:
    def __init__(self, client: Redis, stream: str = "evo:evaluation") -> None:
        self.client = client
        self.stream = stream

    async def enqueue(self, job: EvaluationJob) -> str:
        message_id = await self.client.xadd(self.stream, {"payload": job.model_dump_json()})
        return str(message_id)

    async def acknowledge(self, message_id: str) -> None:
        await self.client.xdel(self.stream, message_id)
