from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import logging
from .config import settings
from .helpers.rabbit_subscriber import start_subscriber
from .helpers.rabbit_publisher import publish_system_error
from .functions.managment import register_device, update_device
from .schemas import Register_Device, Update_Device
from .db import init_db
from .redis_client import init_redis, close_redis
from .routes.device import device_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)
logging.getLogger("pika").setLevel(logging.WARNING)

_main_loop: asyncio.AbstractEventLoop | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _main_loop
    _main_loop = asyncio.get_event_loop()
    logger.info("Starting up Device Service")
    try:
        await init_redis()
        await init_db()
    except Exception as exc:
        logger.error(
            "[Redis] failed to connect.",
            extra={"event": "init_redis", "status": "error", "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user",
        )
    logger.info("Database initialized")
    start_subscribers()
    yield
    await close_redis()
    logger.info("Shutting down Device Service")


app = FastAPI(title="device-service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(device_router)


@app.get("/", tags=["root"])
async def root():
    return {"message": "Device Service"}


# Generico hay que modificar segun el servicio
@app.get("/health", tags=["health"], status_code=status.HTTP_200_OK)
async def health():
    return {"status": "healthy", "service": "device-service"}


EXCHANGE = "ioteur"
QUEUE = "device.register.queue"
ROUTING_KEY = "device.register"

QUEUE_UPDATE = "device.update.queue"
ROUTING_KEY_UPDATE = "device.update"

QUEUE_DELETE = "device.delete.queue"
ROUTING_KEY_DELETE = "device.delete"


def on_device_register(channel, method, properties, body: bytes) -> None:
    event: Register_Device | None = None
    try:
        json_str = body.decode("utf-8", errors="replace").strip()
        event = Register_Device.model_validate_json(json_str)
        future = asyncio.run_coroutine_threadsafe(register_device(event), _main_loop)
        future.result(timeout=30)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        logger.error("Error procesando device.register: %s", exc, exc_info=True)
        asyncio.run_coroutine_threadsafe(
            publish_system_error(
                reason="device_register_failed",
                message=f"Failed to process device.register: {exc}",
            ),
            _main_loop,
        )
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def on_device_update(channel, method, properties, body: bytes) -> None:
    event: Update_Device | None = None
    try:
        json_str = body.decode("utf-8", errors="replace").strip()
        event = Update_Device.model_validate_json(json_str)
        future = asyncio.run_coroutine_threadsafe(update_device(event), _main_loop)
        future.result(timeout=30)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        logger.error("Error procesando device.update: %s", exc, exc_info=True)
        asyncio.run_coroutine_threadsafe(
            publish_system_error(
                reason="device_update_failed",
                message=f"Failed to process device.update: {exc}",
            ),
            _main_loop,
        )
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def on_device_delete(channel, method, properties, body: bytes) -> None:
    from .functions.managment import delete_device
    import json
    try:
        json_str = body.decode("utf-8", errors="replace").strip()
        data = json.loads(json_str)
        device_uuid = data.get("device_uuid")
        if not device_uuid:
            raise ValueError("device_uuid must be provided")
        
        future = asyncio.run_coroutine_threadsafe(delete_device(device_uuid), _main_loop)
        future.result(timeout=30)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        logger.error("Error procesando device.delete: %s", exc, exc_info=True)
        asyncio.run_coroutine_threadsafe(
            publish_system_error(
                reason="device_delete_failed",
                message=f"Failed to process device.delete: {exc}",
            ),
            _main_loop,
        )
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def start_subscribers() -> None:
    start_subscriber(EXCHANGE, QUEUE, ROUTING_KEY, on_device_register)
    start_subscriber(EXCHANGE, QUEUE_UPDATE, ROUTING_KEY_UPDATE, on_device_update)
    start_subscriber(EXCHANGE, QUEUE_DELETE, ROUTING_KEY_DELETE, on_device_delete)
