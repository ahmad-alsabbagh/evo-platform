from typing import Any, Protocol

from redis.asyncio import Redis

from evo_platform.workers.contracts import EvaluationJob


class JobQueue(Protocol):
    async def enqueue(self, job: EvaluationJob) -> str: ...
    async def read(self, consumer: str, count: int = 10) -> list[tuple[str, EvaluationJob]]: ...
    async def acknowledge(self, message_id: str) -> None: ...
    async def claim_stale(
        self, consumer: str, min_idle_ms: int, count: int = 10
    ) -> list[tuple[str, EvaluationJob]]: ...
    async def move_to_dead_letter(
        self, message_id: str, job: EvaluationJob, reason: str
    ) -> None: ...


class RedisStreamQueue:
    def __init__(
        self,
        client: Redis,
        stream: str = "evo:evaluation",
        group: str = "evo-workers",
        dead_letter_stream: str = "evo:evaluation:dlq",
    ) -> None:
        self.client = client
        self.stream = stream
        self.group = group
        self.dead_letter_stream = dead_letter_stream

    async def ensure_group(self) -> None:
        try:
            await self.client.xgroup_create(self.stream, self.group, id="0", mkstream=True)
        except Exception as error:
            if "BUSYGROUP" not in str(error):
                raise

    async def enqueue(self, job: EvaluationJob) -> str:
        message_id = await self.client.xadd(self.stream, {"payload": job.model_dump_json()})
        return message_id.decode() if isinstance(message_id, bytes) else str(message_id)

    async def read(self, consumer: str, count: int = 10) -> list[tuple[str, EvaluationJob]]:
        await self.ensure_group()
        result = await self.client.xreadgroup(
            self.group,
            consumer,
            {self.stream: ">"},
            count=max(1, min(count, 100)),
            block=1000,
        )
        return self._decode(result)

    async def acknowledge(self, message_id: str) -> None:
        await self.client.xack(self.stream, self.group, message_id)

    async def claim_stale(
        self, consumer: str, min_idle_ms: int, count: int = 10
    ) -> list[tuple[str, EvaluationJob]]:
        await self.ensure_group()
        claimed = await self.client.xautoclaim(
            self.stream,
            self.group,
            consumer,
            min_idle_time=max(0, min_idle_ms),
            start_id="0-0",
            count=max(1, min(count, 100)),
        )
        messages = claimed[1] if len(claimed) > 1 else []
        return self._decode([(self.stream, messages)])

    async def move_to_dead_letter(self, message_id: str, job: EvaluationJob, reason: str) -> None:
        await self.client.xadd(
            self.dead_letter_stream,
            {
                "payload": job.model_dump_json(),
                "reason": reason,
                "original_message_id": message_id,
            },
        )
        await self.acknowledge(message_id)

    @staticmethod
    def _decode(result: list[Any]) -> list[tuple[str, EvaluationJob]]:
        def to_text(value: Any) -> str:
            return value.decode() if isinstance(value, bytes) else str(value)

        decoded: list[tuple[str, EvaluationJob]] = []
        for _, messages in result:
            for message_id, fields in messages:
                payload = fields[b"payload"] if b"payload" in fields else fields["payload"]
                decoded.append((to_text(message_id), EvaluationJob.model_validate_json(payload)))
        return decoded
