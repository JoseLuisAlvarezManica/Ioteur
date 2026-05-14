import json
import logging
import uuid

import httpx

from ..helpers.mongo import mongo_client_instance
from ..config import settings
from ..schemas import EmailNotification

logger = logging.getLogger(__name__)


async def handle_device_disconnected(body: bytes) -> None:
    """
    Parse a device.disconnected message, persist an EmailNotification in MongoDB,
    then attempt to send the email via the EmailJS REST API.
    On send success the record is updated to status='sent'.
    """
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(
            "Invalid JSON payload in device.disconnected: %s",
            e,
            extra={"event": "notification.device_disconnected.parse_error"},
        )
        return

    record_id = uuid.uuid4()
    notification = EmailNotification(
        _id=record_id,
        device_id=data.get("device_id"),
        email=data.get("email", ""),
        reason=data.get("reason", ""),
        severity=data.get("severity", "warning"),
        message=data.get("message", ""),
        status="unsent",
    )

    db = mongo_client_instance()[settings.MONGO_NOTIFICATIONS_DB]
    collection = db["email_notifications"]

    # Persist with status=unsent first
    try:
        doc = notification.model_dump(by_alias=True, mode="json")
        await collection.insert_one(doc)
        logger.info(
            "EmailNotification inserted [device_id=%s status=unsent]",
            notification.device_id,
            extra={"event": "notification.device_disconnected.inserted"},
        )
    except Exception as exc:
        logger.error(
            "Failed to insert EmailNotification: %s",
            exc,
            extra={"event": "notification.device_disconnected.insert_failed"},
        )
        return

    # Attempt to send via EmailJS
    template_params = {
        "email": notification.email,
        "device_id": str(notification.device_id),
        "severity": notification.severity,
        "reason": notification.reason,
        "status": notification.status,
        "message": notification.message,
        "created_at": notification.serialize_dt(notification.created_at),
    }

    payload = {
        "service_id": settings.EMAILJS_SERVICE_ID,
        "template_id": settings.EMAILJS_TEMPLATE_ID,
        "user_id": settings.EMAILJS_PUBLIC_KEY,
        "accessToken": settings.EMAILJS_PRIVATE_KEY,
        "template_params": template_params,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(settings.EMAILJS_URL, json=payload)
            response.raise_for_status()

        await collection.update_one(
            {"_id": str(record_id)},
            {"$set": {"status": "sent"}},
        )
        logger.info(
            "Email sent and record updated to 'sent' [device_id=%s]",
            notification.device_id,
            extra={"event": "notification.device_disconnected.email_sent"},
        )
    except httpx.HTTPStatusError as exc:
        logger.error(
            "EmailJS returned error %s for device_id=%s: %s",
            exc.response.status_code,
            notification.device_id,
            exc.response.text,
            extra={"event": "notification.device_disconnected.email_failed"},
        )
    except Exception as exc:
        logger.error(
            "Failed to send email for device_id=%s: %s",
            notification.device_id,
            exc,
            extra={"event": "notification.device_disconnected.email_failed"},
        )
