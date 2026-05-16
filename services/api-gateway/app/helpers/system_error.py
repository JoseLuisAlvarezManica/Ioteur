import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_SERVICE_NAME = "api-gateway"


async def publish_system_error(
    reason: str,
    message: str,
    severity: str = "critical",
    request_id: str | None = None,
) -> None:

    payload = {
        "reason": reason,
        "message": message,
        "severity": severity,
        "service_name": _SERVICE_NAME,
    }
    if request_id:
        payload["request_id"] = request_id
    try:
        async with httpx.AsyncClient(
            base_url=settings.CALL_SERVICE_URL, timeout=5.0
        ) as client:
            await client.post("/system/error", json=payload)
    except Exception as exc:
        logger.error(
            "Could not relay system.error to call-service: %s",
            exc,
            extra={"event": "system.error.relay_failed"},
        )
