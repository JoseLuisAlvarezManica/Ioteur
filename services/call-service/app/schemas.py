from typing import Any

from pydantic import BaseModel


class RegisterDeviceRequest(BaseModel):
    user_id: str
    device_name: str
    mac_address: str
    report_interval: int
    icon: str | None = "sensor"
    color: str | None = "#000000"


class UpdateDeviceRequest(BaseModel):
    device_uuid: str
    report_interval: int | None = None
    status: str | None = None
    icon: str | None = None
    color: str | None = None


class RegisterReceivedRequest(BaseModel):
    device_id: str
    time_procesing: int
    values: dict[str, Any]


class SystemErrorPayload(BaseModel):
    reason: str
    message: str
    severity: str = "critical"
    request_id: str | None = None
    service_name: str | None = None
