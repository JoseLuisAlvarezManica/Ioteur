import redis.asyncio as aioredis
from .config import settings

_redis_pool: aioredis.Redis | None = None


async def init_redis() -> None:
    global _redis_pool
    _redis_pool = aioredis.from_url(
        settings.REDIS_AUTH_URL,
        decode_responses=True,
        encoding="utf-8",
        max_connections=10,
    )


async def close_redis() -> None:
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None


def get_redis() -> aioredis.Redis:
    if _redis_pool is None:
        raise RuntimeError("Redis no inicializado")
    return _redis_pool
