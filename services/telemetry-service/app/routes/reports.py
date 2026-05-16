from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..helpers.mongo import mongo_get_db
from ..schemas import DailyReport

import logging

logger = logging.getLogger(__name__)

telemetry_router = APIRouter(prefix="/reports", tags=["reports"])


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    if isinstance(doc.get("created_at"), datetime):
        doc["created_at"] = doc["created_at"].isoformat()
    return doc


@telemetry_router.get(
    "/{device_id}",
    response_model=list[DailyReport],
    summary="Get the generated daily reports for a device",
)
async def get_reports(
    device_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(mongo_get_db)],
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    cursor = (
        db["daily_reports"]
        .find({"device_id": device_id})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    docs = [doc async for doc in cursor]
    return docs


@telemetry_router.get(
    "/{device_id}/by-date",
    response_model=list[DailyReport],
    summary="Get daily reports for a device filtered by date range",
)
async def get_reports_by_date(
    device_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(mongo_get_db)],
    from_date: Annotated[datetime, Query(alias="from")],
    to_date: Annotated[datetime, Query(alias="to")],
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    cursor = (
        db["daily_reports"]
        .find(
            {
                "device_id": device_id,
                "created_at": {"$gte": from_date, "$lte": to_date},
            }
        )
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    docs = [doc async for doc in cursor]
    return docs
