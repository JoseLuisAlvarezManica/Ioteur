from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer


class RegisterRecord(BaseModel):
    id: UUID = Field(alias="_id")
    device_id: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    time_procesing: int  # seconds
    values: dict[str, Any]

    @field_serializer("id", "device_id")
    def serialize_uuid(self, v: UUID) -> str:
        return str(v)

    model_config = {"populate_by_name": True}


class RegisterRecordResponse(BaseModel):
    id: str
    device_id: str
    created_at: str
    time_procesing: int
    values: dict[str, Any]


class SystemNotification(BaseModel):
    id: UUID = Field(alias="_id")
    request_id: str
    service_name: str = "register-service"
    reason: str
    severity: str  # info | warning | critical
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_serializer("id")
    def serialize_uuid(self, v: UUID) -> str:
        return str(v)

    @field_serializer("created_at")
    def serialize_dt(self, v: datetime) -> str:
        return v.isoformat()

    model_config = {"populate_by_name": True}
