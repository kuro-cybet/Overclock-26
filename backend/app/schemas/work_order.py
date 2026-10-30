from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.auth import UserSummary

class WorkOrderCreate(BaseModel):
    incident_id: str
    title: str
    description: str
    assigned_technician_id: Optional[str] = None
    priority: Optional[str] = "P3"
    required_skills: Optional[List[str]] = []
    sla_deadline: Optional[datetime] = None
    # When true (default) and no technician is supplied, auto-dispatch the best match.
    auto_assign: bool = True

class WorkOrderUpdate(BaseModel):
    status: Optional[str] = None
    diagnosis: Optional[str] = None
    checklist: Optional[List[Dict[str, Any]]] = None
    evidence_notes: Optional[str] = None
    blocked_reason: Optional[str] = None

class WorkOrderReassignRequest(BaseModel):
    new_technician_id: str
    reassignment_reason: str

class WorkOrderRequestReassignment(BaseModel):
    reason: str
    urgency: Optional[str] = "normal"
    notes: Optional[str] = None

class ChecklistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    work_order_id: str
    task_description: str
    step_order: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    completed_by_id: Optional[str] = None
    verification_notes: Optional[str] = None
    verification_status: str

class ChecklistItemUpdate(BaseModel):
    is_completed: bool
    verification_notes: Optional[str] = None

class PartsRequisitionRequest(BaseModel):
    item_id: str
    quantity: int = 1
    justification: Optional[str] = None

class WorkOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    work_order_code: str
    incident_id: str
    title: str
    description: str
    assigned_technician_id: Optional[str] = None
    priority: str
    status: str
    required_skills: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    blocked_reason: Optional[str] = None
    diagnosis: Optional[str] = None
    checklist: Optional[str] = None
    evidence_notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class WorkOrderDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    work_order: WorkOrderResponse
    incident: Optional[Any] = None
    technician: Optional[UserSummary] = None
    reservations: List[Any] = []
    checklists: List[ChecklistItemResponse] = []

class PartsRequisitionResponse(BaseModel):
    status: str
    type: str  # reservation or procurement
    item_name: str
    quantity: int
    work_order_id: str
    message: str
    reservation_id: Optional[str] = None
    procurement_id: Optional[str] = None
    approval_id: Optional[str] = None

class WorkOrderRequestReassignmentResponse(BaseModel):
    status: str
    work_order_id: str
    approval_id: str
    message: str
