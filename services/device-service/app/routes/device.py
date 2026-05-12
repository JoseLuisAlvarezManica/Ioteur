from fastapi import APIRouter, Depends
from ..db import get_db
from ..models import Device
from sqlalchemy.orm import Session

device_router = APIRouter(prefix="/devices", tags=["devices"])


@device_router.get("/", response_model=Device)
def read_devices(db: Session = Depends(get_db)):
    return db.query(Device).all()


@device_router.get("/{user_id}", response_model=Device)
def read_device_by_user_id(user_id: int, db: Session = Depends(get_db)):
    return db.query(Device).filter(Device.user_id == user_id).first()
