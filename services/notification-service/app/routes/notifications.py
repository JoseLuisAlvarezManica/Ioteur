from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..helpers.mongo import mongo_get_db
from ..schemas import EmailNotification

import logging

logger = logging.getLogger(__name__)

notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])


def _serialize(doc: dict) -> dict:
    """Serialize MongoDB document to API response format."""
    # Convert MongoDB ObjectId to string, keeping field name as _id for Pydantic validation
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    if "device_id" in doc:
        doc["device_id"] = str(doc["device_id"])
    if "user_id" in doc and doc["user_id"] is not None:
        doc["user_id"] = str(doc["user_id"])
    # created_at is already stored as ISO string in MongoDB
    if isinstance(doc.get("created_at"), datetime):
        doc["created_at"] = doc["created_at"].isoformat()
    return doc


@notifications_router.get(
    "/device/{device_id}",
    response_model=list[EmailNotification],
    summary="Get email notifications for a specific device",
)
async def get_notifications_by_device(
    device_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(mongo_get_db)],
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    cursor = (
        db["email_notifications"]
        .find({"device_id": device_id})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    docs = [_serialize(doc) async for doc in cursor]
    return docs


@notifications_router.get(
    "/user/{user_id}",
    response_model=list[EmailNotification],
    summary="Get email notifications for a specific user",
)
async def get_notifications_by_user(
    user_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(mongo_get_db)],
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    cursor = (
        db["email_notifications"]
        .find({"user_id": user_id})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    docs = [_serialize(doc) async for doc in cursor]
    return docs
