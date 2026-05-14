"""
Integration tests for notification-service email flow.

Covers:
  - device.disconnected → inserts EmailNotification into MongoDB

Services that must be running:
  notification-service, RabbitMQ, MongoDB (notifications)
"""

import asyncio
import json
import os
import uuid

import aio_pika
import motor.motor_asyncio
import pytest

pytestmark = pytest.mark.email

RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL", "amqp://rabbit_user:rabbit_password@localhost:5672/"
)
MONGO_URL = os.getenv("MONGO_NOTIFICATIONS_URL", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_NOTIFICATIONS_DB", "notifications")
EXCHANGE_NAME = "ioteur"
POLL_INTERVAL = 0.5
POLL_TIMEOUT = 15


async def _publish(routing_key: str, payload: dict) -> None:
    conn = await aio_pika.connect_robust(RABBITMQ_URL)
    async with conn:
        channel = await conn.channel()
        exchange = await channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True
        )
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=routing_key,
        )


def _mongo_client() -> motor.motor_asyncio.AsyncIOMotorClient:
    return motor.motor_asyncio.AsyncIOMotorClient(
        MONGO_URL, serverSelectionTimeoutMS=5000
    )


@pytest.mark.asyncio
async def test_device_disconnected_via_rabbit_persisted():
    device_id = str(uuid.uuid4())
    payload = {
        "device_id": device_id,
        "email": "fake-email@example.test",
        "reason": "missed_intervals",
        "severity": "warning",
        "message": "3 consecutive heartbeats missed.",
    }

    await _publish("device.disconnected", payload)

    mongo = _mongo_client()
    collection = mongo[MONGO_DB]["email_notifications"]

    doc = None
    deadline = asyncio.get_event_loop().time() + POLL_TIMEOUT
    while asyncio.get_event_loop().time() < deadline:
        doc = await collection.find_one({"device_id": device_id})
        if doc:
            break
        await asyncio.sleep(POLL_INTERVAL)

    mongo.close()

    assert doc is not None, (
        f"No email_notification found for device_id={device_id} within {POLL_TIMEOUT}s"
    )
    assert doc["email"] == "fake-email@example.test"
    assert doc["reason"] == "missed_intervals"
    assert doc["status"] in ("sent", "unsent")
