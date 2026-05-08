from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

import logging
from .config import settings


logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up API Gateway")
    yield
    logger.info("Shutting down API Gateway")


app = FastAPI(title="api-gateway", lifespan=lifespan)

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


# Generico hay que modificar segun el servicio
@app.get("/health", tags=["health"], status_code=status.HTTP_200_OK)
async def health():
    return {"status": "healthy", "service": "api-gateway"}
