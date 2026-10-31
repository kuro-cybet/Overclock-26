from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ReportCreate(BaseModel):
    title: str
    description: str
    category: Optional[str] = None
    urgency: Optional[str] = "medium"
    building_id: Optional[str] = None
    room_id: Optional[str] = None
    asset_id: Optional[str] = None
    source: Optional[str] = "web_portal"

class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    report_code: str
    title: str
    description: str
    category: str
    urgency: str
    building_id: str
    room_id: Optional[str] = None
    asset_id: Optional[str] = None
    reporter_id: str
    reporter_role: str
    source: str
    status: str
    incident_id: Optional[str] = None
    ai_extracted_meta: Optional[str] = None
    reporter_name: Optional[str] = None
    building_name: Optional[str] = None
    room_number: Optional[str] = None
    room_name: Optional[str] = None
    asset_tag: Optional[str] = None
    asset_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
