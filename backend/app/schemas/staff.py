from typing import List, Optional
from pydantic import BaseModel

class StaffProfileResponse(BaseModel):
    profile_id: str
    user_id: str
    name: str
    email: str
    sub_role: Optional[str] = None
    shift: Optional[str] = None
    assigned_building_id: Optional[str] = None
    assigned_floor_id: Optional[str] = None
    availability_status: str
    current_workload: int
    skills: List[str] = []

class StaffStatusUpdateRequest(BaseModel):
    status: str

class StaffStatusUpdateResponse(BaseModel):
    user_id: str
    status: str

class EligibleStaffResponse(BaseModel):
    technician_id: str
    name: str
    email: str
    sub_role: Optional[str] = None
    shift: Optional[str] = None
    building_id: Optional[str] = None
    availability_status: str
    current_workload: int
    skills: List[str] = []
    suitability_score: float

