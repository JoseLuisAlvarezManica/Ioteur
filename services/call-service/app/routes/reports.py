import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from ..helpers.call_client import http_get
from ..helpers.rabbit_publisher import publish, publish_system_error
from ..config import settings

logger = logging.getLogger(__name__)

reports_router = APIRouter(prefix="/reports", tags=["reports"])

EXCHANGE = "ioteur"


@reports_router.post("/{device_id}/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_report(device_id: str):
    """Fetch registers for the device then publish a telemetry.report event."""
    try:
        code, data = await http_get(
            settings.REGISTER_SERVICE_URL,
            f"/registers/{device_id}",
            params={"limit": 1000},
        )
        if code != status.HTTP_200_OK:
            logger.warning(
                "register-service returned %d for device %s",
                code,
                device_id,
                extra={"event": "reports.generate.register_error"},
            )
            await publish_system_error(
                reason="upstream_error",
                message=f"register-service GET /registers/{device_id} returned {code}: {data}",
                severity="warning",
            )
            raise HTTPException(status_code=code, detail=data)

        if not data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No hay registros para este dispositivo. No se puede generar el reporte.",
            )

        await publish(
            EXCHANGE,
            "telemetry.report",
            {"device_id": device_id, "records": data},
        )
        logger.info(
            "Queued telemetry.report for device %s (%d records)",
            device_id,
            len(data) if isinstance(data, list) else 0,
            extra={"event": "reports.generate.queued"},
        )
        return {"message": "telemetry.report event queued"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Unexpected error generating report for %s: %s",
            device_id,
            exc,
            extra={"event": "reports.generate.error"},
        )
        await publish_system_error(
            reason="unexpected_error",
            message=f"POST /reports/{device_id}/generate: {exc}",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue telemetry report",
        )


@reports_router.get("/{device_id}")
async def get_reports(
    device_id: str,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    try:
        code, data = await http_get(
            settings.TELEMETRY_SERVICE_URL,
            f"/reports/{device_id}",
            params={"limit": limit, "skip": skip},
        )
        if code != status.HTTP_200_OK:
            logger.warning(
                "telemetry-service returned %d for device %s",
                code,
                device_id,
                extra={"event": "reports.get.upstream_error"},
            )
            await publish_system_error(
                reason="upstream_error",
                message=f"telemetry-service GET /reports/{device_id} returned {code}: {data}",
                severity="warning",
            )
            raise HTTPException(status_code=code, detail=data)
        logger.info(
            "Fetched reports for device %s", device_id, extra={"event": "reports.get"}
        )
        return data
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Unexpected error fetching reports for %s: %s",
            device_id,
            exc,
            extra={"event": "reports.get.error"},
        )
        await publish_system_error(
            reason="unexpected_error", message=f"GET /reports/{device_id}: {exc}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error"
        )


@reports_router.get("/{device_id}/by-date")
async def get_reports_by_date(
    device_id: str,
    from_date: Annotated[datetime, Query(alias="from")],
    to_date: Annotated[datetime, Query(alias="to")],
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    try:
        code, data = await http_get(
            settings.TELEMETRY_SERVICE_URL,
            f"/reports/{device_id}/by-date",
            params={
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
                "limit": limit,
                "skip": skip,
            },
        )
        if code != status.HTTP_200_OK:
            logger.warning(
                "telemetry-service returned %d for device %s (by-date)",
                code,
                device_id,
                extra={"event": "reports.get_by_date.upstream_error"},
            )
            await publish_system_error(
                reason="upstream_error",
                message=f"telemetry-service GET /reports/{device_id}/by-date returned {code}: {data}",
                severity="warning",
            )
            raise HTTPException(status_code=code, detail=data)
        logger.info(
            "Fetched reports by date for device %s",
            device_id,
            extra={"event": "reports.get_by_date"},
        )
        return data
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Unexpected error fetching reports by date for %s: %s",
            device_id,
            exc,
            extra={"event": "reports.get_by_date.error"},
        )
        await publish_system_error(
            reason="unexpected_error",
            message=f"GET /reports/{device_id}/by-date: {exc}",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error"
        )
