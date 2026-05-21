from contextlib import asynccontextmanager

from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import logging

from fastapi.responses import JSONResponse
from .config import settings
from .redis_client import init_redis, close_redis
from .logging_config import JsonFormatter

from .db import engine
from sqlalchemy import text
from .models import Base
from .routes import auth

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
_app_logger = logging.getLogger("app")
_app_logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))
_app_logger.addHandler(handler)
_app_logger.propagate = False

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Starting up Auth Service")
    try:
        await init_redis()
    except Exception as exc:
        logger.error(
            "[Redis] failed to connect.",
            extra={"event": "init_redis", "status": "error", "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user",
        )
    yield
    await close_redis()
    logger.info("Shutting down Auth Service")


app = FastAPI(title="auth-service", lifespan=lifespan)
app.include_router(auth.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"])
async def root():
    return {"message": "Auth Service"}


@app.get("/health", tags=["health"], status_code=status.HTTP_200_OK)
async def health() -> JSONResponse:
    from .redis_client import get_redis

    checks: dict[str, str] = {}

    # Postgres check
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as exc:
        checks["postgres"] = f"error: {exc}"

    # Redis check
    try:
        redis = get_redis()
        pong = await redis.ping()
        checks["redis"] = "ok" if pong else "error: no pong"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    all_ok = all(v == "ok" for v in checks.values())
    http_status = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        content={"status": "ok" if all_ok else "degraded", "checks": checks},
        status_code=http_status,
    )
