from datetime import datetime, timezone
import uuid
from re import match
from sqlalchemy import select

from ..db import AsyncSessionLocal
from ..models import Device
from ..redis_client import get_redis
from ..schemas import (
    Device_Register_Response,
    Register_Device,
    Update_Device,
)

MAC_ADDRESS_REGEX = r"^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$"

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
        
        #Validate mac address format
        if not isinstance(device_data.mac_address, str) or not match(MAC_ADDRESS_REGEX, device_data.mac_address):
            raise ValueError("Invalid MAC address format. Expected format: XX:XX:XX:XX:XX:XX")

        new_device = Device(
            device_uuid=device_uuid,
            user_uuid=device_data.user_id,
            device_name=device_data.device_name,
            mac_address=device_data.mac_address,
            report_interval=device_data.report_interval,
            group=device_data.group,
            icon=device_data.icon,
            color=device_data.color,
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
                "mac_address": new_device.mac_address,
                "device_name": new_device.device_name,
                "user_uuid": new_device.user_uuid,
                "status": new_device.status,
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
            group=new_device.group,
        )


async def update_device(device_data: Update_Device) -> Update_Device:
    async with AsyncSessionLocal() as session:
        device = await session.get(Device, device_data.device_uuid)
        if not device:
            raise ValueError("Dispositivo no encontrado")

        fields_to_update = ["report_interval", "status", "icon", "color", "group"]
        for field in fields_to_update:
            if getattr(device_data, field) is not None:
                setattr(device, field, getattr(device_data, field))

        await session.commit()
        await session.refresh(device)

        redis_client = get_redis()
        await redis_client.hset(
            _device_redis_key(device.device_uuid),
            mapping={"status": device.status},
        )

        return  Update_Device(
            device_uuid=device.device_uuid, 
            status=device.status,
            report_interval=device.report_interval,
            icon=device_data.icon,
            color=device_data.color,
            group=device_data.group
        )


async def delete_device(device_uuid: str) -> None:
    async with AsyncSessionLocal() as session:
        device = await session.get(Device, device_uuid)
        if not device:
            raise ValueError("Device not found")

        await session.delete(device)
        await session.commit()

        redis_client = get_redis()
        await redis_client.delete(_device_redis_key(device_uuid))
