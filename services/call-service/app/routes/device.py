import logging

from fastapi import APIRouter, HTTPException, status

from ..helpers.call_client import http_get
from ..helpers.rabbit_publisher import publish, publish_system_error
from ..config import settings
from ..schemas import RegisterDeviceRequest, UpdateDeviceRequest

logger = logging.getLogger(__name__)

device_router = APIRouter(prefix="/devices", tags=["devices"])

EXCHANGE = "ioteur"


@device_router.post("/register", status_code=status.HTTP_202_ACCEPTED)
async def register_device(body: RegisterDeviceRequest):
    try:
        await publish(EXCHANGE, "device.register", body.model_dump())
        logger.info(
            "Queued device.register for user %s",
            body.user_id,
            extra={"event": "device.register"},
        )
        return {"message": "device.register event queued"}
    except Exception as exc:
        logger.error(
            "Failed to publish device.register: %s",
            exc,
            extra={"event": "device.register.error"},
        )
        await publish_system_error(
            reason="publish_failed",
            message=f"Failed to publish device.register for user {body.user_id}: {exc}",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue event",
        )


@device_router.put("/update", status_code=status.HTTP_202_ACCEPTED)
async def update_device(body: UpdateDeviceRequest):
    try:
        await publish(EXCHANGE, "device.update", body.model_dump(exclude_none=True))
        logger.info(
            "Queued device.update for device %s",
            body.device_uuid,
            extra={"event": "device.update"},
        )
        return {"message": "device.update event queued"}
    except Exception as exc:
        logger.error(
            "Failed to publish device.update: %s",
            exc,
            extra={"event": "device.update.error"},
        )
        await publish_system_error(
            reason="publish_failed",
            message=f"Failed to publish device.update for device {body.device_uuid}: {exc}",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue event",
        )


@device_router.get("/")
async def list_devices():
    try:
        code, data = await http_get(settings.DEVICE_SERVICE_URL, "/devices/")
        if code != status.HTTP_200_OK:
            logger.warning(
                "device-service returned %d on GET /devices/",
                code,
                extra={"event": "device.list.upstream_error"},
            )
            await publish_system_error(
                reason="upstream_error",
                message=f"device-service GET /devices/ returned {code}: {data}",
                severity="warning",
            )
            raise HTTPException(status_code=code, detail=data)
        logger.info("Listed devices", extra={"event": "device.list"})
        return data
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Unexpected error listing devices: %s",
            exc,
            extra={"event": "device.list.error"},
        )
        await publish_system_error(
            reason="unexpected_error", message=f"GET /devices/: {exc}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error"
        )


@device_router.get("/{user_id}")
async def get_device_by_user(user_id: str):
    try:
        code, data = await http_get(settings.DEVICE_SERVICE_URL, f"/devices/{user_id}")
        if code != status.HTTP_200_OK:
            logger.warning(
                "device-service returned %d on GET /devices/%s",
                code,
                user_id,
                extra={"event": "device.get.upstream_error"},
            )
            await publish_system_error(
                reason="upstream_error",
                message=f"device-service GET /devices/{user_id} returned {code}: {data}",
                severity="warning",
            )
            raise HTTPException(status_code=code, detail=data)
        logger.info(
            "Fetched device for user %s", user_id, extra={"event": "device.get"}
        )
        return data
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Unexpected error fetching device %s: %s",
            user_id,
            exc,
            extra={"event": "device.get.error"},
        )
        await publish_system_error(
            reason="unexpected_error", message=f"GET /devices/{user_id}: {exc}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error"
        )
<<<<<<< HEAD


@device_router.delete("/{device_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_device(device_id: str):
    try:
        await publish(EXCHANGE, "device.delete", {"device_uuid": device_id})
        logger.info(
            "Queued device.delete for device %s",
            device_id,
            extra={"event": "device.delete"},
        )
        return {"message": "device.delete event queued"}
    except Exception as exc:
        logger.error(
            "Failed to publish device.delete: %s",
            exc,
            extra={"event": "device.delete.error"},
        )
        await publish_system_error(
            reason="publish_failed",
            message=f"Failed to publish device.delete for device {device_id}: {exc}",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue event",
        )
=======
>>>>>>> features/QA_and_Docs
