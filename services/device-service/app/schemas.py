from pydantic import BaseModel


class Register_Device(BaseModel):
    user_id: str
    device_name: str
    mac_address: str
    report_interval: int
    icon: str | None = "sensor"
    color: str | None = "#000000"
    group: str | None = None


class Device_Register_Response(Register_Device):
    device_uuid: str
    device_name: str
    mac_address: str
    report_interval: int
    icon: str | None = "sensor"
    color: str | None = "#000000"
    group: str | None = None
    status: str
    last_seen: str | None = None


class Update_Device(BaseModel):
    device_uuid: str
    report_interval: int | None = None
    status: str | None = None
    icon: str | None = None
    color: str | None = None
    group: str | None = None


class Get_Status_Response(BaseModel):
    status: str
