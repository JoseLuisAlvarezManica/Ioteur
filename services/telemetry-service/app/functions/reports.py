import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

from ..helpers.mongo import mongo_client_instance
from ..helpers.rabbit_publisher import publish
from ..config import settings
from ..schemas import DailyReport, RegisterRecordResponse, SystemNotification

logger = logging.getLogger(__name__)

EXCHANGE = "ioteur"
ERROR_ROUTING_KEY = "system.error"
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds between retries


async def create_last_day_report(body: bytes, request_id: str) -> DailyReport | None:
    """
    Parse the incoming rabbit payload, fetch telemetry docs for the given device
    over the last 24 hours, and build a schema-backed daily report.
    """

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        logger.error(
            "Invalid JSON payload: %s",
            exc,
            extra={"event": "telemetry.report_parse_error"},
        )
        await _publish_error(
            request_id=request_id,
            reason="invalid_payload",
            severity="critical",
            message=f"Could not parse telemetry report message: {exc}",
        )
        return

    device_id = (
        data.get("device_id")
        or data.get("deviceId")
        or data.get("device_uuid")
        or data.get("deviceUuid")
    )
    user_uuid = data.get("user_uuid") or data.get("userUuid") or data.get("user_id")

    if not device_id:
        logger.error(
            "Rabbit payload is missing a device identifier",
            extra={"event": "telemetry.report_missing_device"},
        )
        await _publish_error(
            request_id=request_id,
            reason="missing_device_id",
            severity="warning",
            message="Telemetry report message did not include a device identifier.",
        )
        return

    client = mongo_client_instance()
    if client is None:
        logger.error(
            "Mongo client is not initialized",
            extra={"event": "telemetry.report_db_unavailable"},
        )
        await _publish_error(
            request_id=request_id,
            reason="mongo_unavailable",
            severity="critical",
            message="Mongo client is not initialized.",
        )
        return

    db = client[settings.MONGO_REGISTER_DB]
    collection = db["telemetry"]
    report_collection = db["daily_reports"]
    cutoff = datetime.now(timezone.utc) - timedelta(days=1)

    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            cursor = (
                collection.find(
                    {
                        "device_id": device_id,
                        "created_at": {"$gte": cutoff},
                    }
                )
                .sort("created_at", -1)
            )
            records = [
                RegisterRecordResponse.model_validate(
                    {
                        "id": str(doc["_id"]),
                        "device_id": doc.get("device_id")
                        or doc.get("deviceId")
                        or device_id,
                        "created_at": doc.get("created_at")
                        or doc.get("createdAt")
                        or datetime.now(timezone.utc),
                        "metric_data": doc.get("metric_data")
                        or doc.get("metricData")
                        or [],
                    }
                )
                async for doc in cursor
            ]
            metric_data = [
                metric
                for record in records
                for metric in record.metric_data
            ]
            report = DailyReport(
                device_id=device_id,
                created_at=datetime.now(timezone.utc),
                metric_data=metric_data,
            )

            report_payload = report.model_dump(by_alias=True)
            insert_exc: Exception | None = None
            for insert_attempt in range(1, MAX_RETRIES + 1):
                try:
                    await report_collection.insert_one(report_payload)
                    logger.info(
                        "Stored daily report for device %s",
                        device_id,
                        extra={
                            "event": "telemetry.report_stored",
                            "device_id": device_id,
                            "user_uuid": user_uuid,
                        },
                    )
                    break
                except Exception as exc:
                    insert_exc = exc
                    logger.warning(
                        "Daily report insert attempt %d/%d failed: %s",
                        insert_attempt,
                        MAX_RETRIES,
                        exc,
                        extra={"event": "telemetry.report_insert_retry"},
                    )
                    if insert_attempt < MAX_RETRIES:
                        await asyncio.sleep(RETRY_DELAY)
            else:
                logger.error(
                    "All %d daily report insert attempts failed",
                    MAX_RETRIES,
                    extra={"event": "telemetry.report_insert_failed"},
                )
                await _publish_error(
                    request_id=request_id,
                    reason="mongo_insert_failed",
                    severity="critical",
                    message=(
                        f"Failed to store daily report for device {device_id} after "
                        f"{MAX_RETRIES} attempts: {insert_exc}"
                    ),
                )
                return None

            logger.info(
                "Loaded %d telemetry documents for device %s",
                len(records),
                device_id,
                extra={
                    "event": "telemetry.report_loaded",
                    "device_id": device_id,
                    "user_uuid": user_uuid,
                },
            )
            return report
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Telemetry report lookup attempt %d/%d failed: %s",
                attempt,
                MAX_RETRIES,
                exc,
                extra={"event": "telemetry.report_lookup_retry"},
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)

    logger.error(
        "All %d telemetry report lookup attempts failed",
        MAX_RETRIES,
        extra={"event": "telemetry.report_lookup_failed"},
    )
    await _publish_error(
        request_id=request_id,
        reason="mongo_lookup_failed",
        severity="critical",
        message=(
            f"Failed to load telemetry documents for device {device_id} after "
            f"{MAX_RETRIES} attempts: {last_exc}"
        ),
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
