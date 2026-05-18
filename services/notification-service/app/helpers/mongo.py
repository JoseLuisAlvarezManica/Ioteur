from collections.abc import AsyncGenerator

import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..config import settings

client: motor.motor_asyncio.AsyncIOMotorClient = None


def mongo_get_client() -> motor.motor_asyncio.AsyncIOMotorClient:
    return motor.motor_asyncio.AsyncIOMotorClient(
        settings.MONGO_NOTIFICATIONS_URL,
        serverSelectionTimeoutMS=5000,
    )


def mongo_client_instance() -> motor.motor_asyncio.AsyncIOMotorClient:
    return client


async def mongo_connect():
    global client
    client = mongo_get_client()


async def mongo_disconnect():
    global client
    if client is not None:
        client.close()
        client = None


async def mongo_get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    db = client[settings.MONGO_NOTIFICATIONS_DB]
    try:
        yield db
    except Exception:
        raise
