import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from functools import partial

import pika

from ..config import settings

logger = logging.getLogger(__name__)

_EXCHANGE = "ioteur"
_SERVICE_NAME = "call-service"


def _blocking_publish(exchange: str, routing_key: str, payload: dict) -> None:
    params = pika.URLParameters(settings.RABBITMQ_URL)
    conn = pika.BlockingConnection(params)
    try:
        channel = conn.channel()
        channel.exchange_declare(
            exchange=exchange, exchange_type="direct", durable=True
        )
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(payload).encode(),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,  # persistent
            ),
        )
        logger.info(
            "Message published to '%s'",
            routing_key,
            extra={"event": "rabbit.publish"},
        )
    finally:
        conn.close()


async def publish(exchange: str, routing_key: str, payload: dict) -> None:
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            None, partial(_blocking_publish, exchange, routing_key, payload)
        )
    except Exception as e:
        logger.error(
            "Failed to publish to '%s': %s",
            routing_key,
            e,
            extra={"event": "rabbit.publish.error"},
        )
        raise


async def publish_system_error(
    reason: str,
    message: str,
    severity: str = "critical",
    request_id: str | None = None,
    service_name: str | None = None,
) -> None:
    payload = {
        "_id": str(uuid.uuid4()),
        "request_id": request_id or str(uuid.uuid4()),
        "service_name": service_name or _SERVICE_NAME,
        "reason": reason,
        "severity": severity,
        "message": message,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await publish(_EXCHANGE, "system.error", payload)
    except Exception as exc:
        logger.error(
            "Could not publish system.error: %s",
            exc,
            extra={"event": "system.error.publish_failed"},
        )
