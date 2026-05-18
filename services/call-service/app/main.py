from contextlib import asynccontextmanager
import asyncio

import pika
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import logging
from .config import settings
from .logging_config import JsonFormatter
from .helpers.redis_client import init_redis, close_redis
from .helpers.scheduler import scheduler_loop
from .routes.device import device_router
from .routes.register import register_router
from .routes.reports import reports_router
from .routes.system import system_router

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
_app_logger = logging.getLogger("app")
_app_logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))
_app_logger.addHandler(handler)
_app_logger.propagate = False

logging.getLogger("pika").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Call Service", extra={"event": "startup"})
    await init_redis()
    _scheduler_task = asyncio.create_task(scheduler_loop())
    logger.info("Scheduler started", extra={"event": "scheduler.start"})
    yield
    _scheduler_task.cancel()
    await asyncio.gather(_scheduler_task, return_exceptions=True)
    await close_redis()
    logger.info("Shutting down Call Service", extra={"event": "shutdown"})


app = FastAPI(title="call-service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(device_router)
app.include_router(register_router)
app.include_router(reports_router)
app.include_router(system_router)


@app.get("/", tags=["root"])
async def root():
    return {"message": "Call Service"}


@app.get("/health", tags=["health"], status_code=status.HTTP_200_OK)
async def health() -> JSONResponse:
    from .helpers.redis_client import get_redis

    checks: dict[str, str] = {}

    # Redis device check
    try:
        redis = get_redis()
        pong = await redis.ping()
        checks["redis_device"] = "ok" if pong else "error: no pong"
    except Exception as exc:
        checks["redis_device"] = f"error: {exc}"

    # RabbitMQ check
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
        checks["rabbitmq"] = "ok"
    except Exception as exc:
        logger.warning(
            "RabbitMQ health check failed: %s", exc, extra={"event": "health.rabbitmq"}
        )
        checks["rabbitmq"] = f"error: {exc}"

    all_ok = all(v == "ok" for v in checks.values())
    http_status = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        content={"status": "ok" if all_ok else "degraded", "checks": checks},
        status_code=http_status,
    )
