# app/models/alert.py
from typing import Optional
from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class LocationPayload(BaseModel):
    mapId: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class RobotAlertPayload(BaseModel):
    robotSn: Optional[str] = None
    robot_sn: Optional[str] = None
    eventId: Optional[str] = None
    event_id: Optional[str] = None
    state: Optional[str] = None
    alert_type: Optional[str] = None
    location: Optional[LocationPayload] = None
    severity: Optional[str] = "MEDIUM"
    timestamp: Optional[str] = None


class Alert(SQLModel, table=True):
    __tablename__ = "alert"

    id: Optional[int] = Field(default=None, primary_key=True)
    robot_sn: str = Field(index=True)
    event_id: Optional[str] = Field(default=None, index=True)
    state: str = Field(index=True)
    map_id: Optional[str] = None
    severity: Optional[str] = "MEDIUM"
    timestamp: str