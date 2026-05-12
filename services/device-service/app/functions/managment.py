from datetime import datetime, timezone
import uuid

from sqlalchemy import select

from ..db import AsyncSessionLocal
from ..models import Device
from ..redis_client import get_redis
from ..schemas import (
    Device_Register_Response,
    Device_Update_Response,
    Register_Device,
    Update_Device,
)


def _device_redis_key(device_uuid: str) -> str:
    return f"device:{device_uuid}"


async def register_device(device_data: Register_Device) -> Device_Register_Response:
    async with AsyncSessionLocal() as session:
        existing_device = await session.scalar(
            select(Device).where(
                Device.mac_address == device_data.mac_address,
                Device.device_name == device_data.device_name,
            )
        )
        if existing_device is not None:
            raise ValueError("Device already exists with the same mac address and name")

        device_uuid = str(uuid.uuid4())
        new_device = Device(
            device_uuid=device_uuid,
            user_uuid=device_data.user_id,
            device_name=device_data.device_name,
            mac_address=device_data.mac_address,
            report_interval=device_data.report_interval,
            status="active",
        )
        session.add(new_device)
        await session.commit()
        await session.refresh(new_device)

        redis_client = get_redis()
        await redis_client.hset(
            _device_redis_key(new_device.device_uuid),
            mapping={
                "device_uuid": new_device.device_uuid,
                "ultima_vez_log": datetime.now(timezone.utc).isoformat(),
            },
        )

        return Device_Register_Response(
            device_uuid=new_device.device_uuid,
            user_id=new_device.user_uuid,
            device_name=new_device.device_name,
            mac_address=new_device.mac_address,
            report_interval=new_device.report_interval,
            status=new_device.status,
        )


async def update_device(device_data: Update_Device) -> Device_Update_Response:
    async with AsyncSessionLocal() as session:
        device = await session.get(Device, device_data.device_uuid)
        if not device:
            raise ValueError("Device not found")

        if device_data.report_interval is not None:
            device.report_interval = device_data.report_interval
        if device_data.status is not None:
            device.status = device_data.status

        await session.commit()
        await session.refresh(device)
        return Device_Update_Response(
            device_uuid=device.device_uuid, status=device.status
        )
