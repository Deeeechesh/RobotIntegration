from pydantic import BaseModel
from typing import Optional

class LocationPayload(BaseModel):
    mapId: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class RobotAlertPayload(BaseModel):
    robotSn: str
    eventId: Optional[str] = None
    state: Optional[str] = None
    alert_type: Optional[str] = None
    location: LocationPayload
    severity: Optional[str] = None
    timestamp: Optional[str] = None
