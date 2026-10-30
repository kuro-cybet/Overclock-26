from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, ConfigDict

class SimulationScenarioEnum(str, Enum):
    exam_room_unavailable = "exam_room_unavailable"
    technician_unavailable = "technician_unavailable"
    stock_shortage = "stock_shortage"
    wifi_outage = "wifi_outage"
    # Canonical aliases supported by simulation engine
    examination_room_unavailable = "examination_room_unavailable"
    technician_absence = "technician_absence"
    critical_part_out_of_stock = "critical_part_out_of_stock"
    multiple_wifi_complaints = "multiple_wifi_complaints"

class SimulationResetResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str
    message: str

class SimulationTriggerResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    scenario: str
    summary: str
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    canonical_incident: Optional[Dict[str, Any]] = None
    individual_reports_preserved: Optional[bool] = None
    eligible_candidates_found: Optional[int] = None
    reassigned_successfully: Optional[bool] = None
    pending_approval_id: Optional[str] = None
    work_order_blocked: Optional[bool] = None
    recovery_options: Optional[List[Dict[str, Any]]] = None
    requires_action: Optional[bool] = None
    affected_work_order: Optional[Dict[str, Any]] = None
    affected_part: Optional[Dict[str, Any]] = None
    affected_building: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, Any]] = None
