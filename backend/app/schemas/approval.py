from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class ApprovalDecisionRequest(BaseModel):
    decision: str  # approved, rejected
    decision_reason: str

class ApprovalResponse(BaseModel):
    id: str
    approval_type: str
    target_entity_type: str
    target_entity_id: str
    requester_id: str
    approver_id: Optional[str] = None
    status: str
    cost_amount: float
    justification: str
    decision_reason: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

