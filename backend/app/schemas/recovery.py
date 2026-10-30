from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class RecoveryPlanRequest(BaseModel):
    disruption_type: str  # exam_room_unavailable, technician_absent, stock_shortage, wifi_outage
    entity_id: str
    constraints: Optional[Dict[str, Any]] = None

class RecoveryOption(BaseModel):
    option_id: str
    title: str
    description: str
    impact_assessment: str
    feasibility_score: float
    requires_approval: bool
    approval_role: Optional[str] = None
    target_action: str
    action_payload: Dict[str, Any]

class RecoveryPlanResponse(BaseModel):
    disruption_type: str
    entity_id: str
    current_impact: str
    options: List[RecoveryOption]

class RecoveryExecuteRequest(BaseModel):
    option_id: str
    target_action: str
    action_payload: Dict[str, Any]
    approval_override: bool = False

class RecoveryInitiateRequest(BaseModel):
    disruption_type: str
    incident_id: Optional[str] = None
    chosen_plan_id: str
    actions: List[Dict[str, Any]] = []
