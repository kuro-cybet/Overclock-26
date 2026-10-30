from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, ConfigDict

class RecoveryPlanConstraints(BaseModel):
    max_travel_distance_meters: Optional[float] = None
    required_equipment: Optional[List[str]] = None
    min_capacity: Optional[int] = None
    preferred_building_id: Optional[str] = None
    allow_overtime: Optional[bool] = None
    budget_limit: Optional[float] = None

class RecoveryActionPayload(BaseModel):
    booking_id: Optional[str] = None
    new_room_id: Optional[str] = None
    original_room_id: Optional[str] = None
    work_order_id: Optional[str] = None
    new_technician_id: Optional[str] = None
    item_id: Optional[str] = None
    quantity: Optional[int] = None
    estimated_cost: Optional[float] = None
    recipients: Optional[List[str]] = None
    title: Optional[str] = None
    message: Optional[str] = None
    reason: Optional[str] = None

class RecoveryPlanRequest(BaseModel):
    disruption_type: str  # exam_room_unavailable, technician_absent, stock_shortage, wifi_outage
    entity_id: str
    constraints: Optional[Union[RecoveryPlanConstraints, Dict[str, Any]]] = None

class RecoveryOption(BaseModel):
    option_id: str
    title: str
    description: str
    impact_assessment: str
    feasibility_score: float
    requires_approval: bool
    approval_role: Optional[str] = None
    target_action: str
    action_payload: Union[RecoveryActionPayload, Dict[str, Any]]

class RecoveryPlanResponse(BaseModel):
    disruption_type: str
    entity_id: str
    current_impact: str
    options: List[RecoveryOption]

class RecoveryExecuteRequest(BaseModel):
    option_id: str
    target_action: str
    action_payload: Union[RecoveryActionPayload, Dict[str, Any]]
    approval_override: bool = False

class RecoveryExecuteResponse(BaseModel):
    status: str
    message: str
    booking_id: Optional[str] = None
    work_order_id: Optional[str] = None
    procurement_id: Optional[str] = None

class RecoveryActionSpec(BaseModel):
    action_type: str
    target_entity_type: str
    target_entity_id: str
    payload: Union[RecoveryActionPayload, Dict[str, Any]]

class RecoveryInitiateRequest(BaseModel):
    disruption_type: str
    incident_id: Optional[str] = None
    chosen_plan_id: str
    actions: List[Union[RecoveryActionSpec, Dict[str, Any]]] = []

class RecoveryInitiateResponse(BaseModel):
    execution_id: str
    disruption_type: str
    chosen_plan_id: Optional[str] = None
    status: str
    verification_status: str

class RecoveryRunActionsResponse(BaseModel):
    execution_id: str
    status: str
    actions_executed: List[Dict[str, Any]] = []

class RecoveryVerifyResponse(BaseModel):
    execution_id: str
    verification_status: str
    is_success: bool
    outcome_summary: Optional[str] = None
    checks_passed: List[str] = []
    checks_failed: List[str] = []
    incident_status: Optional[str] = None

class RecoveryExecutionSummary(BaseModel):
    id: str
    incident_id: Optional[str] = None
    disruption_type: str
    chosen_plan_id: Optional[str] = None
    status: str
    verification_status: str
    verification_outcome: Optional[str] = None
    verified_at: Optional[str] = None
    created_at: Optional[str] = None
    actions_count: int
