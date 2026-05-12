import logging
from collections.abc import Callable, Awaitable

import aio_pika
import aio_pika.abc

from ..config import settings

logger = logging.getLogger(__name__)

_connection: aio_pika.abc.AbstractRobustConnection | None = None
_consumer_tag: str | None = None


async def start_subscriber(
    exchange: str,
    queue: str,
    routing_key: str,
    on_message: Callable[[aio_pika.abc.AbstractIncomingMessage], Awaitable[None]],
) -> None:
    global _connection, _consumer_tag
    _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await _connection.channel()
    await channel.set_qos(prefetch_count=1)
    exch = await channel.declare_exchange(
        exchange, aio_pika.ExchangeType.DIRECT, durable=True
    )
    q = await channel.declare_queue(queue, durable=True)
    await q.bind(exch, routing_key=routing_key)
    _consumer_tag = await q.consume(on_message, no_ack=False)
    logger.info(
        "Listening on routing key '%s' via queue '%s'",
        routing_key,
        queue,
        extra={"event": "rabbit.subscriber.started"},
    )


async def stop_subscriber() -> None:
    global _connection
    if _connection and not _connection.is_closed:
        await _connection.close()
        logger.info(
            "Subscriber disconnected.", extra={"event": "rabbit.subscriber.stopped"}
        )
        _connection = None
