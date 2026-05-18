import asyncio
import logging
import uuid
from datetime import datetime, timezone

from ..config import settings
from .call_client import http_get
from .rabbit_publisher import publish, publish_system_error

from .redis_client import get_redis

logger = logging.getLogger(__name__)

_EXCHANGE = "ioteur"


def _device_redis_key(device_uuid: str) -> str:
    return f"device:{device_uuid}"


async def check_inactive_devices() -> None:
    """
    Scans all active devices in Redis and marks as inactive those whose
    last telemetry timestamp exceeded 3 * report_interval seconds ago.
    Publishes device.update (to sync PostgreSQL) and device.disconnected
    (to trigger email notification) for each inactive device found.
    """
    redis = get_redis()
    now = datetime.now(timezone.utc)

    # Scan all device keys directly in Redis — no HTTP call needed
    async for key in redis.scan_iter("device:*"):
        try:
            fields = await redis.hgetall(key)
        except Exception as exc:
            logger.error(
                "scheduler: failed to hgetall for key %s: %s",
                key,
                exc,
                extra={"event": "scheduler.redis_read.error"},
            )
            continue

        # Only process active devices
        if fields.get("status") != "active":
            continue

        device_uuid = fields.get("device_uuid")
        user_uuid = fields.get("user_uuid")
        device_name = fields.get("device_name", device_uuid)
        ultima_vez_log_raw = fields.get("ultima_vez_log")
        report_interval_raw = fields.get("report_interval")

        if not device_uuid or not user_uuid:
            logger.warning(
                "scheduler: key %s missing device_uuid or user_uuid, skipping",
                key,
                extra={"event": "scheduler.missing_fields"},
            )
            continue

        if not report_interval_raw:
            # Device was registered before report_interval was cached in Redis.
            # Fetch it from device-service and backfill Redis for future cycles.
            logger.warning(
                "scheduler: device %s has no report_interval in Redis, fetching from device-service",
                device_uuid,
                extra={"event": "scheduler.missing_interval.backfill"},
            )
            try:
                code, dev_data = await http_get(
                    settings.DEVICE_SERVICE_URL, "/devices/"
                )
                if code == 200 and isinstance(dev_data, list):
                    match = next(
                        (d for d in dev_data if d.get("device_uuid") == device_uuid),
                        None,
                    )
                    if match:
                        report_interval_raw = str(match["report_interval"])
                        await redis.hset(key, "report_interval", report_interval_raw)
                        logger.info(
                            "scheduler: backfilled report_interval=%s for device %s",
                            report_interval_raw,
                            device_uuid,
                            extra={"event": "scheduler.missing_interval.backfilled"},
                        )
            except Exception as exc:
                logger.error(
                    "scheduler: could not backfill report_interval for device %s: %s",
                    device_uuid,
                    exc,
                    extra={"event": "scheduler.missing_interval.backfill_error"},
                )

            if not report_interval_raw:
                logger.warning(
                    "scheduler: could not resolve report_interval for device %s, skipping",
                    device_uuid,
                    extra={"event": "scheduler.missing_interval.skip"},
                )
                continue

        try:
            interval = int(report_interval_raw)
        except ValueError:
            logger.warning(
                "scheduler: invalid report_interval '%s' for device %s, skipping",
                report_interval_raw,
                device_uuid,
                extra={"event": "scheduler.invalid_interval"},
            )
            continue

        if not ultima_vez_log_raw:
            logger.warning(
                "scheduler: device %s has no ultima_vez_log, skipping",
                device_uuid,
                extra={"event": "scheduler.missing_timestamp"},
            )
            continue

        try:
            ultima_vez_log = datetime.fromisoformat(ultima_vez_log_raw)
            if ultima_vez_log.tzinfo is None:
                ultima_vez_log = ultima_vez_log.replace(tzinfo=timezone.utc)
        except ValueError as exc:
            logger.warning(
                "scheduler: invalid ultima_vez_log for device %s: %s",
                device_uuid,
                exc,
                extra={"event": "scheduler.invalid_timestamp"},
            )
            continue

        elapsed = (now - ultima_vez_log).total_seconds()
        threshold = 3 * interval

        if elapsed <= threshold:
            continue

        logger.info(
            "scheduler: device %s inactive (elapsed=%.0fs threshold=%ds), marking inactive",
            device_uuid,
            elapsed,
            threshold,
            extra={"event": "scheduler.device_inactive", "device_uuid": device_uuid},
        )

        # --- 3a. Update Redis immediately ---
        try:
            await redis.hset(key, "status", "inactive")
        except Exception as exc:
            logger.error(
                "scheduler: failed to update Redis status for %s: %s",
                device_uuid,
                exc,
                extra={"event": "scheduler.redis_update.error"},
            )
            continue

        # --- 3b. Publish device.update so device-service syncs PostgreSQL ---
        try:
            await publish(
                _EXCHANGE,
                "device.update",
                {"device_uuid": device_uuid, "status": "inactive"},
            )
        except Exception as exc:
            logger.error(
                "scheduler: failed to publish device.update for %s: %s",
                device_uuid,
                exc,
                extra={"event": "scheduler.device_update.publish.error"},
            )
            await publish_system_error(
                reason="scheduler_publish_failed",
                message=f"Failed to publish device.update for {device_uuid}: {exc}",
            )
            # Continue to attempt email notification regardless

        # --- 3c. Fetch user email from auth-service ---
        email = ""
        try:
            auth_code, auth_data = await http_get(
                settings.AUTH_SERVICE_URL, f"/auth/user/{user_uuid}"
            )
            if auth_code == 200 and isinstance(auth_data, dict):
                email = auth_data.get("email", "")
            else:
                logger.warning(
                    "scheduler: auth-service returned %d for user %s",
                    auth_code,
                    user_uuid,
                    extra={"event": "scheduler.auth_lookup.warning"},
                )
        except Exception as exc:
            logger.error(
                "scheduler: could not fetch email for user %s: %s",
                user_uuid,
                exc,
                extra={"event": "scheduler.auth_lookup.error"},
            )

        # --- 3d. Publish device.disconnected to trigger email notification ---
        try:
            await publish(
                _EXCHANGE,
                "device.disconnected",
                {
                    "_id": str(uuid.uuid4()),
                    "device_id": device_uuid,
                    "email": email,
                    "reason": "inactivity_timeout",
                    "severity": "warning",
                    "message": (
                        f"Device '{device_name}' has not sent telemetry for "
                        f"{elapsed:.0f}s (threshold: {threshold}s). "
                        "It has been marked as inactive."
                    ),
                },
            )
        except Exception as exc:
            logger.error(
                "scheduler: failed to publish device.disconnected for %s: %s",
                device_uuid,
                exc,
                extra={"event": "scheduler.device_disconnected.publish.error"},
            )
            await publish_system_error(
                reason="scheduler_publish_failed",
                message=f"Failed to publish device.disconnected for {device_uuid}: {exc}",
            )


async def scheduler_loop() -> None:
    """Background loop that periodically checks for inactive devices."""
    logger.info(
        "scheduler: loop starting (interval=%ds)",
        settings.SCHEDULER_INTERVAL_SECONDS,
        extra={"event": "scheduler.loop.start"},
    )
    while True:
        await asyncio.sleep(settings.SCHEDULER_INTERVAL_SECONDS)
        try:
            await check_inactive_devices()
        except Exception as exc:
            logger.error(
                "scheduler: unhandled error in check cycle: %s",
                exc,
                extra={"event": "scheduler.loop.error"},
            )
