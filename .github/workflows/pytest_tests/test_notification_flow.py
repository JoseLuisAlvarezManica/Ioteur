"""
Integration tests for notification-service.

Covers:
  - system.error  → inserts SystemNotification into MongoDB (system_notifications)

Services that must be running:
  notification-service, RabbitMQ, MongoDB (notifications)

"""

import asyncio
import json
import os
import uuid

import aio_pika
import httpx
import motor.motor_asyncio
import pytest

pytestmark = pytest.mark.system

RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL", "amqp://rabbit_user:rabbit_password@localhost:5672/"
)
NOTIFICATION_BASE_URL = "http://localhost:8004"
MONGO_URL = os.getenv("MONGO_NOTIFICATIONS_URL", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_NOTIFICATIONS_DB", "notifications")
EXCHANGE_NAME = "ioteur"
POLL_INTERVAL = 0.5
POLL_TIMEOUT = 15


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _publish(
    routing_key: str, payload: dict, request_id: str | None = None
) -> None:
    conn = await aio_pika.connect_robust(RABBITMQ_URL)
    async with conn:
        channel = await conn.channel()
        exchange = await channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True
        )
        headers = {"request_id": request_id} if request_id else {}
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode(),
                headers=headers,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=routing_key,
        )


def _mongo_client() -> motor.motor_asyncio.AsyncIOMotorClient:
    return motor.motor_asyncio.AsyncIOMotorClient(
        MONGO_URL, serverSelectionTimeoutMS=5000
    )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient(base_url=NOTIFICATION_BASE_URL) as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["checks"]["mongo"] == "healthy"
    assert body["checks"]["rabbitmq"] == "healthy"


# ---------------------------------------------------------------------------
# system.error → system_notifications collection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_system_error_persisted():
    request_id = str(uuid.uuid4())
    payload = {
        "request_id": request_id,
        "service_name": "test-service",
        "reason": "test_reason",
        "severity": "critical",
        "message": "Integration test error message",
    }

    await _publish("system.error", payload, request_id=request_id)

    mongo = _mongo_client()
    collection = mongo[MONGO_DB]["system_notifications"]

    doc = None
    deadline = asyncio.get_event_loop().time() + POLL_TIMEOUT
    while asyncio.get_event_loop().time() < deadline:
        doc = await collection.find_one({"request_id": request_id})
        if doc:
            break
        await asyncio.sleep(POLL_INTERVAL)

    mongo.close()

    assert doc is not None, (
        f"No system_notification found for request_id={request_id} within {POLL_TIMEOUT}s"
    )
    assert doc["service_name"] == "test-service"
    assert doc["reason"] == "test_reason"
    assert doc["severity"] == "critical"
    assert doc["message"] == "Integration test error message"
    assert "created_at" in doc
