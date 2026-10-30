from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class RoomResponse(BaseModel):
    id: str
    building_id: str
    floor_id: str
    room_number: str
    name: str
    type: str
    capacity: int
    features: Optional[str] = None
    status: str
    daily_readiness_status: str
    readiness_checked_at: Optional[datetime] = None
    readiness_checked_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class RoomReadinessUpdate(BaseModel):
    daily_readiness_status: str  # confirmed, stale, unconfirmed
    notes: Optional[str] = None

