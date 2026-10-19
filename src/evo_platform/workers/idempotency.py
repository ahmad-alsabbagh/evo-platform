from redis.asyncio import Redis


class RedisIdempotencyStore:
    def __init__(self, client: Redis, prefix: str = "evo:idempotency:") -> None:
        self.client = client
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    async def claim(self, key: str, ttl_seconds: int) -> bool:
        result = await self.client.set(self._key(key), "claimed", nx=True, ex=ttl_seconds)
        return bool(result)

    async def release(self, key: str) -> None:
        await self.client.delete(self._key(key))

    async def complete(self, key: str, ttl_seconds: int) -> None:
        await self.client.set(self._key(key), "completed", ex=ttl_seconds)
