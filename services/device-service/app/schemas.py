from pydantic import BaseModel


class Register_Device(BaseModel):
    user_id: str
    device_name: str
    mac_address: str
    report_interval: int

class Device_Register_Response(Register_Device):
    device_uuid: str
    status: str

class Update_Device(BaseModel):
    device_uuid: str
    report_interval: int | None = None
    status: str | None = None

class Device_Update_Response(BaseModel):
    device_uuid: str
    status: str
