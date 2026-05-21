import json
import logging
import uuid

from ..helpers.mongo import mongo_client_instance
from ..config import settings
from ..schemas import SystemNotification

logger = logging.getLogger(__name__)


async def handle_system_error(body: bytes, request_id: str) -> None:
    """
    Parse a system.error message and persist it as a SystemNotification
    in the 'system_notifications' MongoDB collection.
    """
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(
            "Invalid JSON payload in system.error: %s",
            e,
            extra={"event": "notification.system_error.parse_error"},
        )
        return

    notification = SystemNotification(
        _id=uuid.uuid4(),
        request_id=data.get("request_id", request_id),
        service_name=data.get("service_name", "unknown"),
        reason=data.get("reason", ""),
        severity=data.get("severity", "info"),
        message=data.get("message", ""),
    )

    db = mongo_client_instance()[settings.MONGO_NOTIFICATIONS_DB]
    collection = db["system_notifications"]

    try:
        doc = notification.model_dump(by_alias=True, mode="json")
        await collection.insert_one(doc)
        logger.info(
            "SystemNotification inserted [service=%s reason=%s]",
            notification.service_name,
            notification.reason,
            extra={"event": "notification.system_error.inserted"},
        )
    except Exception as exc:
        logger.error(
            "Failed to insert SystemNotification: %s",
            exc,
            extra={"event": "notification.system_error.insert_failed"},
        )
