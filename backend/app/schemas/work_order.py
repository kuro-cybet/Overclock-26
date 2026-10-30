from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class WorkOrderCreate(BaseModel):
    incident_id: str
    title: str
    description: str
    assigned_technician_id: Optional[str] = None
    priority: Optional[str] = "P3"
    required_skills: Optional[List[str]] = []
    sla_deadline: Optional[datetime] = None

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
    id: str
    work_order_id: str
    task_description: str
    step_order: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    completed_by_id: Optional[str] = None
    verification_notes: Optional[str] = None
    verification_status: str

    class Config:
        from_attributes = True

class ChecklistItemUpdate(BaseModel):
    is_completed: bool
    verification_notes: Optional[str] = None

class PartsRequisitionRequest(BaseModel):
    item_id: str
    quantity: int = 1
    justification: Optional[str] = None

class WorkOrderResponse(BaseModel):
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

    class Config:
        from_attributes = True
