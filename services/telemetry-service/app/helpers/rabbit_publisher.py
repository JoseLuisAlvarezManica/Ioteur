import asyncio
import json
import logging
from functools import partial

import pika

from ..config import settings

logger = logging.getLogger(__name__)


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
    """Publish a JSON message to a direct exchange (runs blocking pika in a thread)."""
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
