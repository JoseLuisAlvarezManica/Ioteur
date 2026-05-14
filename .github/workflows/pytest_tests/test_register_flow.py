"""
Integration test: publishes a device.register message via aio-pika,
waits for register-service to consume and persist it, then verifies
the record via the HTTP endpoint.

"""

import asyncio
import json
import os
import uuid

import aio_pika
import httpx
import pytest

RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL", "amqp://rabbit_user:rabbit_password@localhost:5672/"
)
REGISTER_BASE_URL = os.getenv("REGISTER_BASE_URL", "http://localhost:8005")
EXCHANGE_NAME = "ioteur"
ROUTING_KEY = "device.register"
POLL_INTERVAL = 0.5
POLL_TIMEOUT = 15


@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient(base_url=REGISTER_BASE_URL) as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["checks"]["mongo"] == "healthy"
    assert body["checks"]["rabbitmq"] == "healthy"


@pytest.mark.asyncio
async def test_register_flow():
    device_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    values = {"temperature": 22.5, "humidity": 55}
    payload = {"device_id": device_id, "time_procesing": 3, "values": values}

    # 1. Publish device.register
    conn = await aio_pika.connect_robust(RABBITMQ_URL)
    async with conn:
        channel = await conn.channel()
        exchange = await channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True
        )
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode(),
                headers={"request_id": request_id},
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=ROUTING_KEY,
        )

    # 2. Poll GET /registers/{device_id}
    record = None
    async with httpx.AsyncClient(base_url=REGISTER_BASE_URL) as client:
        deadline = asyncio.get_event_loop().time() + POLL_TIMEOUT
        while asyncio.get_event_loop().time() < deadline:
            resp = await client.get(f"/registers/{device_id}")
            assert resp.status_code == 200
            records = resp.json()
            if records:
                record = records[0]
                break
            await asyncio.sleep(POLL_INTERVAL)

    assert record is not None, (
        f"No register found for device {device_id} within {POLL_TIMEOUT}s"
    )
    assert record["device_id"] == device_id
    assert record["values"] == values
    assert record["time_procesing"] == 3
    assert "id" in record
    assert "created_at" in record


@pytest.mark.asyncio
async def test_unknown_device_returns_empty():
    unknown_id = str(uuid.uuid4())
    async with httpx.AsyncClient(base_url=REGISTER_BASE_URL) as client:
        resp = await client.get(f"/registers/{unknown_id}")
    assert resp.status_code == 200
    assert resp.json() == []
