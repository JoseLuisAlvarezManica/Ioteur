import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status

from ..config import settings
from ..decorators import bearer_scheme, must_be_admin, must_be_logged_in
from ..helpers.call_client import CallClient, get_call_client
from ..schemas import RegisterDevice, RegisterReceived, SystemErrorPayload, UpdateDevice

logger = logging.getLogger(__name__)

router = APIRouter(tags=["call"])

call_dep = Annotated[CallClient, Depends(get_call_client)]


async def verify_internal_key(
    x_internal_key: Annotated[str | None, Header()] = None,
) -> None:
    if x_internal_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


# --- Devices ---


@router.post(
    "/devices/register",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_logged_in
async def register_device(request: Request, body: RegisterDevice, client: call_dep):
    code, data = await client.post("/devices/register", body.model_dump())
    if code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.put(
    "/devices/update",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_logged_in
async def update_device(request: Request, body: UpdateDevice, client: call_dep):
    code, data = await client.put("/devices/update", body.model_dump(exclude_none=True))
    if code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.get(
    "/devices/",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_admin
async def list_devices(request: Request, client: call_dep):
    code, data = await client.get("/devices/")
    if code != status.HTTP_200_OK:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.get(
    "/devices/{user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_logged_in
async def get_device_by_user(request: Request, user_id: str, client: call_dep):
    code, data = await client.get(f"/devices/{user_id}")
    if code != status.HTTP_200_OK:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.delete(
    "/devices/{device_id}",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_logged_in
async def delete_device(request: Request, device_id: str, client: call_dep):
    code, data = await client.delete(f"/devices/{device_id}")
    if code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=code, detail=data)
    return data


# --- Registers ---


@router.post(
    "/registers/received",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_logged_in
async def register_received(request: Request, body: RegisterReceived, client: call_dep):
    code, data = await client.post("/registers/received", body.model_dump())
    if code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.get(
    "/registers/{device_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_logged_in
async def get_registers(
    request: Request,
    device_id: str,
    client: call_dep,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    code, data = await client.get(
        f"/registers/{device_id}", params={"limit": limit, "skip": skip}
    )
    if code != status.HTTP_200_OK:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.get(
    "/registers/{device_id}/by-date",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_logged_in
async def get_registers_by_date(
    request: Request,
    device_id: str,
    client: call_dep,
    from_date: Annotated[datetime, Query(alias="from")],
    to_date: Annotated[datetime, Query(alias="to")],
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    code, data = await client.get(
        f"/registers/{device_id}/by-date",
        params={
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "limit": limit,
            "skip": skip,
        },
    )
    if code != status.HTTP_200_OK:
        raise HTTPException(status_code=code, detail=data)
    return data


# --- System ---


@router.post(
    "/system/error",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_internal_key)],
)
async def relay_system_error(body: SystemErrorPayload, client: call_dep):
    """Internal relay — forwards a system.error from any service to call-service → RabbitMQ."""
    code, data = await client.post("/system/error", body.model_dump(exclude_none=True))
    if code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=code, detail=data)
    return data


# --- Reports ---


@router.post(
    "/reports/{device_id}/generate",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_logged_in
async def generate_report(request: Request, device_id: str, client: call_dep):
    code, data = await client.post(f"/reports/{device_id}/generate", {})
    if code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.get(
    "/reports/{device_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_logged_in
async def get_reports(
    request: Request,
    device_id: str,
    client: call_dep,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    code, data = await client.get(
        f"/reports/{device_id}", params={"limit": limit, "skip": skip}
    )
    if code != status.HTTP_200_OK:
        raise HTTPException(status_code=code, detail=data)
    return data


@router.get(
    "/reports/{device_id}/by-date",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(bearer_scheme)],
)
@must_be_logged_in
async def get_reports_by_date(
    request: Request,
    device_id: str,
    client: call_dep,
    from_date: Annotated[datetime, Query(alias="from")],
    to_date: Annotated[datetime, Query(alias="to")],
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    code, data = await client.get(
        f"/reports/{device_id}/by-date",
        params={
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "limit": limit,
            "skip": skip,
        },
    )
    if code != status.HTTP_200_OK:
        raise HTTPException(status_code=code, detail=data)
    return data
