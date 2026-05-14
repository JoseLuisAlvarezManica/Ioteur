import logging
import threading
from collections.abc import Callable

import pika

from ..config import settings

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_threads: list[threading.Thread] = []
_connections: list[pika.BlockingConnection] = []


def _run_consumer(
    exchange: str,
    queue: str,
    routing_key: str,
    on_message: Callable[
        [pika.adapters.blocking_connection.BlockingChannel, object, object, bytes], None
    ],
) -> None:
    params = pika.URLParameters(settings.RABBITMQ_URL)
    params.heartbeat = 0
    conn = pika.BlockingConnection(params)
    with _lock:
        _connections.append(conn)
    channel = conn.channel()
    channel.exchange_declare(exchange=exchange, exchange_type="direct", durable=True)
    channel.queue_declare(queue=queue, durable=True)
    channel.queue_bind(queue=queue, exchange=exchange, routing_key=routing_key)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue, on_message_callback=on_message)
    logger.info(
        "Listening on routing key '%s' via queue '%s'",
        routing_key,
        queue,
        extra={"event": "rabbit.subscriber.started"},
    )
    channel.start_consuming()


def start_subscriber(
    exchange: str,
    queue: str,
    routing_key: str,
    on_message: Callable[
        [pika.adapters.blocking_connection.BlockingChannel, object, object, bytes], None
    ],
) -> None:
    thread = threading.Thread(
        target=_run_consumer,
        args=(exchange, queue, routing_key, on_message),
        daemon=True,
        name=f"rabbit-consumer-{routing_key}",
    )
    with _lock:
        _threads.append(thread)
    thread.start()


def stop_subscriber() -> None:
    with _lock:
        for conn in _connections:
            try:
                if not conn.is_closed:
                    conn.close()
            except Exception:
                pass
        _connections.clear()
        _threads.clear()
    logger.info(
        "All subscribers disconnected.", extra={"event": "rabbit.subscriber.stopped"}
    )
