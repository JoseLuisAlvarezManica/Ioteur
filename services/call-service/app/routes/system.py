import logging

from fastapi import APIRouter, status

from ..helpers.rabbit_publisher import publish_system_error
from ..schemas import SystemErrorPayload

logger = logging.getLogger(__name__)

system_router = APIRouter(prefix="/system", tags=["system"])


@system_router.post("/error", status_code=status.HTTP_202_ACCEPTED)
async def report_system_error(body: SystemErrorPayload):
    await publish_system_error(
        reason=body.reason,
        message=body.message,
        severity=body.severity,
        request_id=body.request_id,
        service_name=body.service_name,
    )
    logger.info(
        "Relayed system.error from %s: %s",
        body.service_name or "unknown",
        body.reason,
        extra={"event": "system.error.relayed"},
    )
    return {"message": "system.error event queued"}
