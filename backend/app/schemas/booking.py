from typing import Optional, List, Dict, Any, Union, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class BookingCreate(BaseModel):
    room_id: str
    title: str
    purpose: str  # lecture, lab_session, examination, meeting, seminar
    start_time: datetime
    end_time: datetime
    equipment_required: Optional[List[str]] = []

class ExamReadinessChecklist(BaseModel):
    hvac_check: bool = True
    power_check: bool = True
    seating_check: bool = True
    av_check: bool = True
    acoustics_check: Optional[bool] = None
    lighting_check: Optional[bool] = None

class ExamReadinessInspectionRequest(BaseModel):
    status: Literal["ready", "fault_detected"]
    checklist: Union[ExamReadinessChecklist, Dict[str, bool]]
    notes: Optional[str] = None
    reported_faults: Optional[List[str]] = None

class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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

class ExaminationSessionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    booking_code: str
    title: str
    purpose: str
    start_time: str
    end_time: str
    hours_remaining: float
    room_id: Optional[str] = None
    room_number: str
    room_name: str
    building_name: str
    room_status: Optional[str] = "available"
    daily_readiness_status: Optional[str] = "uninspected"
    equipment_required: Optional[str] = None
    has_open_incident: bool
    incident_title: Optional[str] = None
    status: str

class ExamReadinessResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str
    readiness_status: str
    booking_id: str
    message: str
    room_number: str
    inspected_by: str
    timestamp: str
    incident_code: Optional[str] = None
