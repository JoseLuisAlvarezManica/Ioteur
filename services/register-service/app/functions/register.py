import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from ..helpers.mongo import mongo_client_instance
from ..helpers.rabbit_publisher import publish
from ..config import settings
from ..schemas import RegisterRecord, SystemNotification

logger = logging.getLogger(__name__)

EXCHANGE = "ioteur"
ERROR_ROUTING_KEY = "system.error"
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds between retries


async def handle_device_register(body: bytes, request_id: str) -> None:
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(
            "Invalid JSON payload: %s",
            e,
            extra={"event": "register.parse_error"},
        )
        await _publish_error(
            request_id=request_id,
            reason="invalid_payload",
            severity="critical",
            message=f"Could not parse device.register message: {e}",
        )
        return

    record = RegisterRecord(
        _id=uuid.uuid4(),
        device_id=data.get("device_id"),
        time_procesing=data.get("time_procesing", 0),
        values=data.get("values", {}),
    )

    db = mongo_client_instance()[settings.MONGO_REGISTER_DB]
    collection = db["register"]

    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            doc = record.model_dump(by_alias=True, mode="json")
            await collection.insert_one(doc)
            logger.info(
                "Register inserted on attempt %d",
                attempt,
                extra={"event": "register.inserted"},
            )
            return
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Insert attempt %d/%d failed: %s",
                attempt,
                MAX_RETRIES,
                exc,
                extra={"event": "register.insert_retry"},
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)

    logger.error(
        "All %d insert attempts failed, publishing error",
        MAX_RETRIES,
        extra={"event": "register.insert_failed"},
    )
    await _publish_error(
        request_id=request_id,
        reason="mongo_insert_failed",
        severity="critical",
        message=f"Failed to insert register record after {MAX_RETRIES} attempts: {last_exc}",
    )


async def _publish_error(
    request_id: str, reason: str, severity: str, message: str
) -> None:
    notification = SystemNotification(
        _id=uuid.uuid4(),
        request_id=request_id,
        reason=reason,
        severity=severity,
        message=message,
        created_at=datetime.now(timezone.utc),
    )
    try:
        await publish(
            exchange=EXCHANGE,
            routing_key=ERROR_ROUTING_KEY,
            payload=notification.model_dump(by_alias=True),
        )
    except Exception as exc:
        logger.error(
            "Could not publish system.error: %s",
            exc,
            extra={"event": "register.error_publish_failed"},
        )
