from datetime import datetime, timezone

from ..db import AsyncSessionLocal
from ..redis_client import get_redis


def _device_redis_key(device_uuid: str) -> str:
    return f"device:{device_uuid}"

async def validate_mac_address(mac_address: str) -> bool:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            "SELECT COUNT(*) FROM devices WHERE mac_address = :mac_address",
            {"mac_address": mac_address}
        )
        count = result.scalar_one()
        return count == 0

async def validate_device_uuid(device_uuid: str) -> bool:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            "SELECT COUNT(*) FROM devices WHERE device_uuid = :device_uuid",
            {"device_uuid": device_uuid}
        )
        count = result.scalar_one()

        if count > 0:
            redis_client = get_redis()
            await redis_client.hset(
                _device_redis_key(device_uuid),
                mapping={"ultima_vez_log": datetime.now(timezone.utc).isoformat()},
            )

        return count > 0