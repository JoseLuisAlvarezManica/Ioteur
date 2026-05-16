import asyncio
import uuid
from contextlib import asynccontextmanager

import pika
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import logging
from .config import settings
from .helpers.mongo import mongo_client_instance, mongo_connect, mongo_disconnect
from .helpers.rabbit_subscriber import start_subscriber, stop_subscriber
from .helpers.rabbit_publisher import publish
from .functions.reports import create_last_day_report
from .routes.reports import telemetry_router
from .logging_config import JsonFormatter

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    handlers=[handler],
)

for _noisy in ("pymongo", "pika"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

_main_loop: asyncio.AbstractEventLoop | None = None


def _on_create_report(channel, method, properties, body: bytes) -> None:
    request_id = (properties.headers or {}).get("request_id") or str(uuid.uuid4())
    try:
        future = asyncio.run_coroutine_threadsafe(
            create_last_day_report(body, request_id), _main_loop
        )
        report = future.result(timeout=30)
        
        # Send notification
        publish_future = asyncio.run_coroutine_threadsafe(
            publish(
                exchange="ioteur",
                routing_key="report.created",
                payload={
                    "request_id": request_id,
                    "message": "Report created successfully",
                    "status": "success"
                }
            ),
            _main_loop
        )
        publish_future.result(timeout=10)
        
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        logger.error(
            "Unhandled error processing report creation: %s",
            exc,
            extra={"event": "reports.handler_error"},
        )
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _main_loop
    _main_loop = asyncio.get_event_loop()
    logger.info("Starting up Telemetry Service", extra={"event": "startup"})
    await mongo_connect()
    start_subscriber(
        exchange="ioteur",
        queue="telemetry.reports.create",
        routing_key="telemetry.report",
        on_message=_on_create_report,
    )
    yield
    stop_subscriber()
    await mongo_disconnect()
    logger.info("Shutting down Telemetry Service", extra={"event": "shutdown"})


app = FastAPI(title="telemetry-service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry_router)


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

    # RabbitMQ connection check
    def _check_rabbitmq() -> None:
        params = pika.URLParameters(settings.RABBITMQ_URL)
        params.socket_timeout = 3
        conn = pika.BlockingConnection(params)
        conn.close()

    try:
        await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, _check_rabbitmq),
            timeout=3,
        )
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
