from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class BookingCreate(BaseModel):
    room_id: str
    title: str
    purpose: str  # lecture, lab_session, examination, meeting, seminar
    start_time: datetime
    end_time: datetime
    equipment_required: Optional[List[str]] = []

class ExamReadinessInspectionRequest(BaseModel):
    status: str  # ready, fault_detected
    checklist: Dict[str, bool]
    notes: Optional[str] = None
    reported_faults: Optional[List[str]] = None

class BookingResponse(BaseModel):
    id: str
    booking_code: str
    room_id: str
    user_id: str
    user_role: str
    title: str
    purpose: str
    start_time: datetime
    end_time: datetime
    status: str
    equipment_required: Optional[str] = None
    conflict_resolved_to_room_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
