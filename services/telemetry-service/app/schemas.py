from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class MetricData(BaseModel):
    model_config = {"populate_by_name": True}

    device_name: str
    value_list: list[str] = Field(..., alias="valueList")
    percentaje_change: float = Field(..., alias="percentajeChange")
    top_value: str = Field(..., alias="topValue")
    most_frequent_value: str = Field(..., alias="mostFrequentValue")


class DailyReport(BaseModel):
    model_config = {"populate_by_name": True}

    device_id: str = Field(..., alias="deviceId")
    created_at: datetime = Field(..., alias="createdAt")
    metric_data: list[MetricData] = Field(..., alias="metricData")


class RegisterRecordResponse(BaseModel):
    id: str
    device_id: str = Field(..., alias="deviceId")
    created_at: datetime = Field(..., alias="createdAt")
    metric_data: list[MetricData] = Field(..., alias="metricData")


class SystemNotification(BaseModel):
    id: UUID = Field(..., alias="_id")
    request_id: str
    reason: str
    severity: str
    message: str
    created_at: datetime
    service_name: str = "telemetry-service"

    model_config = {"populate_by_name": True}
