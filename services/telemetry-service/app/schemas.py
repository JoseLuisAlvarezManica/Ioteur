from pydantic import BaseModel, Field
from datetime import datetime


class MetricData(BaseModel):
    device_name: str
    value_list: list[str] = Field(..., alias="valueList")
    percentaje_change: float = Field(..., alias="percentajeChange")
    top_value: str = Field(..., alias="topValue")
    most_frequent_value: str = Field(..., alias="mostFrequentValue")


class DailyReport(BaseModel):
    device_id: str = Field(..., alias="deviceId")
    created_at: datetime = Field(..., alias="createdAt")
    metric_data: list[MetricData] = Field(..., alias="metricData")


class RegisterRecordResponse(BaseModel):
    id: str
    device_id: str = Field(..., alias="deviceId")
    created_at: datetime = Field(..., alias="createdAt")
    metric_data: list[MetricData] = Field(..., alias="metricData")
