import json
import logging

import aio_pika

from ..config import settings

logger = logging.getLogger(__name__)


async def publish(exchange: str, routing_key: str, payload: dict) -> None:
    """Publish a JSON message to a direct exchange (async)."""
    try:
        conn = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        async with conn:
            channel = await conn.channel()
            exch = await channel.declare_exchange(
                exchange, aio_pika.ExchangeType.DIRECT, durable=True
            )
            await exch.publish(
                aio_pika.Message(
                    body=json.dumps(payload).encode(),
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=routing_key,
            )
        logger.info(
            "Message published to '%s'",
            routing_key,
            extra={"event": "rabbit.publish"},
        )
    except aio_pika.exceptions.AMQPConnectionError as e:
        logger.error(
            "Failed to publish to '%s': %s",
            routing_key,
            e,
            extra={"event": "rabbit.publish.error"},
        )
        raise
