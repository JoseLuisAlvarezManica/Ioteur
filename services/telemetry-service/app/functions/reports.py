import asyncio
import json
import logging
import uuid
from collections import Counter
from datetime import datetime, timezone

from ..helpers.mongo import mongo_client_instance
from ..helpers.rabbit_publisher import publish
from ..config import settings
from ..schemas import DailyReport, MetricData, SystemNotification

logger = logging.getLogger(__name__)

EXCHANGE = "ioteur"
ERROR_ROUTING_KEY = "system.error"
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds between retries


def _compute_metrics(records: list[dict]) -> list[MetricData]:
    """Aggregate per-metric statistics from raw register records."""
    metric_values: dict[str, list[str]] = {}
    for record in records:
        for key, val in record.get("values", {}).items():
            metric_values.setdefault(key, []).append(str(val))

    metrics: list[MetricData] = []
    for name, values in metric_values.items():
        if not values:
            continue
        try:
            floats = [float(v) for v in values]
            first, last = floats[0], floats[-1]
            pct_change = round((last - first) / first * 100, 2) if first != 0.0 else 0.0
            top = str(max(floats))
        except (ValueError, ZeroDivisionError):
            pct_change = 0.0
            top = values[0]
        most_freq = Counter(values).most_common(1)[0][0]
        metrics.append(
            MetricData(
                device_name=name,
                value_list=values,
                percentaje_change=pct_change,
                top_value=top,
                most_frequent_value=most_freq,
            )
        )
    return metrics


async def create_last_day_report(body: bytes, request_id: str) -> DailyReport | None:
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
        return None

    device_id = (
        data.get("device_id")
        or data.get("deviceId")
        or data.get("device_uuid")
        or data.get("deviceUuid")
    )
    user_uuid = data.get("user_uuid") or data.get("userUuid") or data.get("user_id")
    records: list[dict] = data.get("records", [])

    if not records:
        logger.warning(
            "No records in telemetry payload for device %s, skipping report",
            device_id,
            extra={"event": "telemetry.report_no_records"},
        )
        return None

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
        return None

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
        return None

    db = client[settings.MONGO_TELEMETRY_DB]
    report_collection = db["daily_reports"]

    metrics = _compute_metrics(records)
    report = DailyReport(
        device_id=device_id,
        created_at=datetime.now(timezone.utc),
        metric_data=metrics,
    )
    # Store with Python field names so GET queries by device_id work
    report_payload = report.model_dump()

    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await report_collection.insert_one(report_payload)
            logger.info(
                "Stored daily report for device %s (%d metrics, %d records)",
                device_id,
                len(metrics),
                len(records),
                extra={
                    "event": "telemetry.report_stored",
                    "device_id": device_id,
                    "user_uuid": user_uuid,
                },
            )
            return report
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Daily report insert attempt %d/%d failed: %s",
                attempt,
                MAX_RETRIES,
                exc,
                extra={"event": "telemetry.report_insert_retry"},
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)

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
            f"{MAX_RETRIES} attempts: {last_exc}"
        ),
    )
    return None


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
