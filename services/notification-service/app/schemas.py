from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer


class SystemNotification(BaseModel):
    id: UUID = Field(alias="_id")
    request_id: str
    service_name: str
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


class EmailNotification(BaseModel):
    id: UUID = Field(alias="_id")
    device_id: UUID
    email: str
    reason: str
    severity: str  # info | warning | critical
    message: str
    status: str = "unsent"  # sent | unsent
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_serializer("id", "device_id")
    def serialize_uuid(self, v: UUID) -> str:
        return str(v)

    @field_serializer("created_at")
    def serialize_dt(self, v: datetime) -> str:
        return v.isoformat()

    model_config = {"populate_by_name": True}

    model_config = {"populate_by_name": True}
