from contextlib import asynccontextmanager
import threading
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import logging
from .config import settings
from .helpers.rabbit_subscriber import start_subscriber
from .functions.managment import register_device, update_device
from .schemas import Register_Device, Update_Device
from .db import init_db
from asyncio import new_event_loop, set_event_loop
from .redis_client import init_redis, close_redis
from .routes.device import device_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)
logging.getLogger("pika").setLevel(logging.WARNING)

@asynccontextmanager
async def lifespan(app: FastAPI):
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

EXCHANGE = "devices"
QUEUE = "device.register.queue"
ROUTING_KEY = "device.register"

QUEUE_UPDATE = "device.update.queue"
ROUTING_KEY_UPDATE = "device.update"

_loop = None

def on_device_register(channel, method, properties, body: bytes) -> None:
    global _loop
    if _loop is None:
        _loop = new_event_loop()
        set_event_loop(_loop)

    event: Register_Device | None = None
    try:
        # Decode bytes to string with error handling
        json_str = body.decode('utf-8', errors='replace').strip()
        event = Register_Device.model_validate_json(json_str)
        _loop.run_until_complete(register_device(event))
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        logger.error("Error procesando device.register: %s", exc, exc_info=True)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def on_device_update(channel, method, properties, body: bytes) -> None:
    global _loop
    if _loop is None:
        _loop = new_event_loop()
        set_event_loop(_loop)
    event: Update_Device | None = None
    try:
        # Decode bytes to string with error handling
        json_str = body.decode('utf-8', errors='replace').strip()
        event = Update_Device.model_validate_json(json_str)
        _loop.run_until_complete(update_device(event))
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        logger.error("Error procesando device.update: %s", exc, exc_info=True)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def start_subscribers():
    """Start RabbitMQ subscribers in background thread"""
    start_subscriber(EXCHANGE, QUEUE, ROUTING_KEY, on_device_register)
    start_subscriber(EXCHANGE, QUEUE_UPDATE, ROUTING_KEY_UPDATE, on_device_update)
    threading.Event().wait()

subscriber_thread = threading.Thread(target=start_subscribers, daemon=True)
subscriber_thread.start()
