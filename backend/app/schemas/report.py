from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

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
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

