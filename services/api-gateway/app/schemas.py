# Esquema para actualización de usuario (PUT)
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, model_validator


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None


class UserSelfUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    old_password: Optional[str] = None
    new_password: Optional[str] = None

    @model_validator(mode="after")
    def check_password_fields(self) -> "UserSelfUpdate":
        if (self.old_password is None) != (self.new_password is None):
            raise ValueError(
                "Both old_password and new_password must be provided together"
            )
        return self


class SignUp(BaseModel):
    name: str
    email: str
    password: str


class Login(BaseModel):
    email: str
    password: str


class User(BaseModel):
    username: str
    email: EmailStr
    role: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class RefreshRequest(BaseModel):
    access_token: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    name: str
    email: EmailStr
    role: str


class UserIdResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str


# --- Call Service ---


class RegisterDevice(BaseModel):
    device_name: str
    mac_address: str
    report_interval: int
    icon: str | None = "sensor"
    color: str | None = "#000000"
    group: str | None = None


class UpdateDevice(BaseModel):
    device_uuid: str
    report_interval: int | None = None
    status: str | None = None
    icon: str | None = None
    color: str | None = None
    group: str | None = None


class RegisterReceived(BaseModel):
    device_id: str
    time_procesing: int
    values: dict[str, Any]


class SystemErrorPayload(BaseModel):
    reason: str
    message: str
    severity: str = "critical"
    request_id: str | None = None
    service_name: str | None = None
