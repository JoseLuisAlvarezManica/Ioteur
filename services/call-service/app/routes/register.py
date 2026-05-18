import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from ..helpers.call_client import http_get
from ..helpers.rabbit_publisher import publish, publish_system_error
from ..helpers.redis_client import get_redis
from ..config import settings
from ..schemas import RegisterReceivedRequest

logger = logging.getLogger(__name__)

register_router = APIRouter(prefix="/registers", tags=["registers"])

EXCHANGE = "ioteur"


def _device_redis_key(device_id: str) -> str:
    return f"device:{device_id}"


@register_router.post("/received", status_code=status.HTTP_202_ACCEPTED)
async def register_received(body: RegisterReceivedRequest):
    current_status: str | None = None
    try:
        redis = get_redis()
        key = _device_redis_key(body.device_id)
        if not await redis.exists(key):
            logger.warning(
                "Device %s not found in Redis, rejecting register",
                body.device_id,
                extra={"event": "register.received.device_not_found"},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {body.device_id} is not registered",
            )

        current_status = await redis.hget(key, "status")
        redis_update: dict[str, str] = {
            "ultima_vez_log": datetime.now(timezone.utc).isoformat()
        }

        if current_status == "inactive":
            redis_update["status"] = "active"
            logger.info(
                "Device %s reconnected, restoring status to active",
                body.device_id,
                extra={"event": "device.reconnected"},
            )

        await redis.hset(key, mapping=redis_update)
        logger.info(
            "Updated device.connected for %s",
            body.device_id,
            extra={"event": "device.connected"},
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to update device.connected for %s: %s",
            body.device_id,
            exc,
            extra={"event": "device.connected.error"},
        )
        await publish_system_error(
            reason="redis_write_failed",
            message=f"Failed to update device.connected for {body.device_id}: {exc}",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update device state",
        )

    try:
        if current_status == "inactive":
            await publish(
                EXCHANGE,
                "device.update",
                {"device_uuid": body.device_id, "status": "active"},
            )
            logger.info(
                "Queued device.update (active) for reconnected device %s",
                body.device_id,
                extra={"event": "device.reactivated"},
            )
        await publish(EXCHANGE, "register.received", body.model_dump())
        logger.info(
            "Queued register.received for device %s",
            body.device_id,
            extra={"event": "register.received"},
        )
        return {"message": "register.received event queued"}
    except Exception as exc:
        logger.error(
            "Failed to publish register.received for %s: %s",
            body.device_id,
            exc,
            extra={"event": "register.received.error"},
        )
        await publish_system_error(
            reason="publish_failed",
            message=f"Failed to publish register.received for device {body.device_id}: {exc}",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue event",
        )


@register_router.get("/{device_id}")
async def get_registers(
    device_id: str,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    try:
        code, data = await http_get(
            settings.REGISTER_SERVICE_URL,
            f"/registers/{device_id}",
            params={"limit": limit, "skip": skip},
        )
        if code != status.HTTP_200_OK:
            logger.warning(
                "register-service returned %d for device %s",
                code,
                device_id,
                extra={"event": "registers.get.upstream_error"},
            )
            await publish_system_error(
                reason="upstream_error",
                message=f"register-service GET /registers/{device_id} returned {code}: {data}",
                severity="warning",
            )
            raise HTTPException(status_code=code, detail=data)
        logger.info(
            "Fetched registers for device %s",
            device_id,
            extra={"event": "registers.get"},
        )
        return data
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Unexpected error fetching registers for %s: %s",
            device_id,
            exc,
            extra={"event": "registers.get.error"},
        )
        await publish_system_error(
            reason="unexpected_error", message=f"GET /registers/{device_id}: {exc}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error"
        )


@register_router.get("/{device_id}/by-date")
async def get_registers_by_date(
    device_id: str,
    from_date: Annotated[datetime, Query(alias="from")],
    to_date: Annotated[datetime, Query(alias="to")],
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    try:
        code, data = await http_get(
            settings.REGISTER_SERVICE_URL,
            f"/registers/{device_id}/by-date",
            params={
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
                "limit": limit,
                "skip": skip,
            },
        )
        if code != status.HTTP_200_OK:
            logger.warning(
                "register-service returned %d for device %s (by-date)",
                code,
                device_id,
                extra={"event": "registers.get_by_date.upstream_error"},
            )
            await publish_system_error(
                reason="upstream_error",
                message=f"register-service GET /registers/{device_id}/by-date returned {code}: {data}",
                severity="warning",
            )
            raise HTTPException(status_code=code, detail=data)
        logger.info(
            "Fetched registers by date for device %s",
            device_id,
            extra={"event": "registers.get_by_date"},
        )
        return data
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Unexpected error fetching registers by date for %s: %s",
            device_id,
            exc,
            extra={"event": "registers.get_by_date.error"},
        )
        await publish_system_error(
            reason="unexpected_error",
            message=f"GET /registers/{device_id}/by-date: {exc}",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error"
        )
