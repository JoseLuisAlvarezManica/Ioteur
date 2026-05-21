from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db import get_db
from ..models import Device
from ..schemas import Device_Register_Response, Get_Status_Response

device_router = APIRouter(prefix="/devices", tags=["devices"])


def _to_response(device: Device) -> Device_Register_Response:
    return Device_Register_Response(
        device_uuid=device.device_uuid,
        user_id=device.user_uuid,
        device_name=device.device_name,
        mac_address=device.mac_address,
        report_interval=device.report_interval,
        status=device.status,
        icon=device.icon,
        color=device.color,
        group=device.group,
    )


@device_router.get("/", response_model=list[Device_Register_Response])
async def read_devices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device))
    return [_to_response(d) for d in result.scalars().all()]


@device_router.get("/{user_id}", response_model=list[Device_Register_Response])
async def read_device_by_user_id(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.user_uuid == user_id))
    devices = result.scalars().all()
    if not devices:
        return []
    return [_to_response(d) for d in devices]


@device_router.get("/status/{device_id}", response_model=Get_Status_Response)
async def read_device_by_id(device_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.device_uuid == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return Get_Status_Response(status=device.status)
