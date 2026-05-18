from pydantic import BaseModel


class Register_Device(BaseModel):
    user_id: str
    device_name: str
    mac_address: str
    report_interval: int
    icon: str | None = "sensor"
    color: str | None = "#000000"


class Device_Register_Response(Register_Device):
    device_uuid: str
    status: str


class Update_Device(BaseModel):
    device_uuid: str
    report_interval: int | None = None
    status: str | None = None
    icon: str | None = None
    color: str | None = None


class Device_Update_Response(BaseModel):
    device_uuid: str
    status: str
    icon: str | None = None
    color: str | None = None
