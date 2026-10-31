from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.report import ReportResponse
from app.schemas.work_order import WorkOrderResponse

class IncidentCreate(BaseModel):
    title: str
    description: str
    category: str
    severity: Optional[str] = "medium"
    priority: Optional[str] = "P3"
    building_id: str
    room_id: Optional[str] = None
    asset_id: Optional[str] = None

class IncidentCorrelateRequest(BaseModel):
    report_ids: List[str]
    target_incident_id: Optional[str] = None
    new_title: Optional[str] = None

class IncidentMergeRequest(BaseModel):
    primary_incident_id: str
    duplicate_incident_ids: List[str]
    notes: Optional[str] = None

class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_code: str
    title: str
    description: str
    category: str
    severity: str
    priority: str
    building_id: str
    room_id: Optional[str] = None
    asset_id: Optional[str] = None
    status: str
    sla_due_at: Optional[datetime] = None
    is_sla_breached: bool
    correlated_count: int
    summary: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class IncidentDetailsResponse(BaseModel):
    incident: IncidentResponse
    reports: List[ReportResponse] = []
    work_orders: List[WorkOrderResponse] = []
