from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

import logging

from fastapi.responses import JSONResponse
from .logging_config import JsonFormatter
from .config import settings
from .redis_client import init_redis, close_redis

from .routes import auth, call

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
_app_logger = logging.getLogger("app")
_app_logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))
_app_logger.addHandler(handler)
_app_logger.propagate = False

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

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
    logger.info("Shutting down API Gateway Service")


app = FastAPI(
    title="api-gateway",
    lifespan=lifespan,
    docs_url=None,  # desactiva /docs
    redoc_url=None,  # desactiva /redoc
    openapi_url=None,  # desactiva /openapi.json
)

app.include_router(auth.router)
app.include_router(call.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"])
async def root():
    return {"message": "API GATEWAY"}


@app.get("/health", tags=["health"], status_code=status.HTTP_200_OK)
async def health() -> JSONResponse:
    from .redis_client import get_redis

    checks: dict[str, str] = {}

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
