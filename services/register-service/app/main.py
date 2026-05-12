import asyncio
import uuid
from contextlib import asynccontextmanager

import aio_pika
import aio_pika.abc
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import logging
from .config import settings
from .helpers.mongo import mongo_client_instance, mongo_connect, mongo_disconnect
from .helpers.rabbit_subscriber import start_subscriber, stop_subscriber
from .functions.register import handle_device_register
from .routes.register import register_router
from .logging_config import JsonFormatter

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    handlers=[handler],
)

for _noisy in ("pymongo", "aiormq", "aio_pika"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def _on_device_register(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    request_id = (message.headers or {}).get("request_id") or str(uuid.uuid4())
    try:
        await handle_device_register(message.body, request_id)
        await message.ack()
    except Exception as exc:
        logger.error(
            "Unhandled error processing device.register: %s",
            exc,
            extra={"event": "register.handler_error"},
        )
        await message.nack(requeue=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Register Service", extra={"event": "startup"})
    await mongo_connect()
    await start_subscriber(
        exchange="ioteur",
        queue="register.device.register",
        routing_key="device.register",
        on_message=_on_device_register,
    )
    yield
    await stop_subscriber()
    await mongo_disconnect()
    logger.info("Shutting down Register Service", extra={"event": "shutdown"})


app = FastAPI(title="register-service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(register_router)


@app.get("/", tags=["root"])
async def root():
    return {"message": "Register Service"}


@app.get("/health", tags=["health"])
async def health():
    checks: dict[str, str] = {}

    # MongoDB ping
    try:
        await asyncio.wait_for(
            mongo_client_instance().admin.command("ping"),
            timeout=3,
        )
        checks["mongo"] = "healthy"
    except Exception as e:
        logger.warning(
            "MongoDB health check failed: %s", e, extra={"event": "health.mongo"}
        )
        checks["mongo"] = "unhealthy"

    # RabbitMQ connection check (async)
    try:
        conn = await asyncio.wait_for(
            aio_pika.connect(settings.RABBITMQ_URL),
            timeout=3,
        )
        await conn.close()
        checks["rabbitmq"] = "healthy"
    except Exception as e:
        logger.warning(
            "RabbitMQ health check failed: %s", e, extra={"event": "health.rabbitmq"}
        )
        checks["rabbitmq"] = "unhealthy"

    all_healthy = all(v == "healthy" for v in checks.values())
    http_status = (
        status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(
        status_code=http_status,
        content={"status": "healthy" if all_healthy else "unhealthy", "checks": checks},
    )
