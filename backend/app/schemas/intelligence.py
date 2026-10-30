from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class HistoricalCaseResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    category: str
    symptoms: str
    diagnosis: str
    resolution_steps: str
    parts_used: List[str] = []
    root_cause: Optional[str] = None
    similarity_score: float

class PredictiveAlertResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    alert_type: str
    affected_entity_type: str
    affected_entity_id: str
    title: str
    evidence_refs: str
    trigger_threshold: str
    predicted_window: str
    confidence: float
    status: str
    deduplication_key: str
    recommended_action: str

class BuildingClusterResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    building_id: str
    building_name: str
    building_code: Optional[str] = None
    active_incident_count: Optional[int] = None
    incident_count: Optional[int] = None
    categories: List[str] = []
    highest_priority: Optional[str] = None
    severity: Optional[str] = None
    recommended_action: Optional[str] = None
    incident_codes: List[str] = []
    is_cluster: Optional[bool] = None
    risk_level: Optional[str] = None

class RoomAtRiskResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    room_id: str
    room_number: str
    building_name: str
    room_status: str
    daily_readiness_status: str
    active_incidents_count: Optional[int] = None
    pending_work_orders_count: Optional[int] = None
    upcoming_bookings_count: Optional[int] = None
    next_booking_time: Optional[str] = None
    risk_severity: Optional[str] = None
    recommended_action: Optional[str] = None

class AffectedExaminationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    booking_id: str
    booking_code: str
    title: str
    room_id: str
    room_number: str
    building_name: str
    start_time: str
    hours_until_exam: Optional[float] = None
    critical_threat: Optional[str] = None
    threat_details: Optional[str] = None
    recommended_contingency: Optional[str] = None

class DecisionExplanationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    decision_type: str
    entity_type: str
    entity_id: str
    chosen_option: str
    explanation_text: str
    confidence_score: float
    factors: Optional[str] = None
    created_at: Optional[str] = None

class OperationalAssessmentResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    timestamp: str
    overall_campus_health: Optional[str] = None
    risk_score: Optional[float] = None
    summary: Optional[Dict[str, Any]] = None
    building_clusters: List[BuildingClusterResponse] = []
    rooms_at_risk: List[RoomAtRiskResponse] = []
    examination_threats: List[AffectedExaminationResponse] = []
    technician_workload_risks: List[Dict[str, Any]] = []
    critical_inventory_shortages: List[Dict[str, Any]] = []
    sla_breach_projections: List[Dict[str, Any]] = []
    repeated_asset_failures: List[Dict[str, Any]] = []
