import logging

from fastapi import APIRouter, HTTPException, Query, status

from ..helpers.call_client import http_get
from ..helpers.rabbit_publisher import publish_system_error
from ..config import settings

logger = logging.getLogger(__name__)

notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])


@notifications_router.get("/device/{device_id}", status_code=status.HTTP_200_OK)
async def get_notifications_by_device(
    device_id: str,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    try:
        code, data = await http_get(
            settings.NOTIFICATION_SERVICE_URL,
            f"/notifications/device/{device_id}",
            params={"limit": limit, "skip": skip},
        )
        if code != status.HTTP_200_OK:
            await publish_system_error(
                reason="upstream_error",
                message=f"notification-service GET /notifications/device/{device_id} returned {code}: {data}",
                severity="warning",
            )
            raise HTTPException(status_code=code, detail=data)
        return data
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Unexpected error fetching notifications for device %s: %s",
            device_id,
            exc,
            extra={"event": "notifications.get_by_device.error"},
        )
        await publish_system_error(
            reason="unexpected_error",
            message=f"GET /notifications/device/{device_id}: {exc}",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error"
        )


@notifications_router.get("/user/{user_id}", status_code=status.HTTP_200_OK)
async def get_notifications_by_user(
    user_id: str,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    try:
        code, data = await http_get(
            settings.NOTIFICATION_SERVICE_URL,
            f"/notifications/user/{user_id}",
            params={"limit": limit, "skip": skip},
        )
        if code != status.HTTP_200_OK:
            await publish_system_error(
                reason="upstream_error",
                message=f"notification-service GET /notifications/user/{user_id} returned {code}: {data}",
                severity="warning",
            )
            raise HTTPException(status_code=code, detail=data)
        return data
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Unexpected error fetching notifications for user %s: %s",
            user_id,
            exc,
            extra={"event": "notifications.get_by_user.error"},
        )
        await publish_system_error(
            reason="unexpected_error",
            message=f"GET /notifications/user/{user_id}: {exc}",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error"
        )
