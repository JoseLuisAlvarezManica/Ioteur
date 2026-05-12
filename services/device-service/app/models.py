from sqlalchemy import CheckConstraint, String, DateTime, Integer, Interval
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .db import Base


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = (
        CheckConstraint("report_interval > 0", name="check_report_interval_positive"),
    )

    device_uuid: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_uuid: Mapped[str] = mapped_column(String(36), nullable=False)
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mac_address: Mapped[str] = mapped_column(String(17), nullable=False, unique=True)
    report_interval: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    last_seen: Mapped[Interval] = mapped_column(Interval, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, nullable=False, default=datetime.now()
    )
