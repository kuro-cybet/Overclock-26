from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")

    id: str
    asset_tag: str
    name: str
    category: str
    building_id: str
    room_id: str
    status: str
    serial_number: Optional[str] = None
    last_inspected_at: Optional[datetime] = None
    created_at: datetime

class AssetPredictiveHealthMetrics(BaseModel):
    model_config = ConfigDict(extra="allow")

    age_years: float
    expected_lifespan_years: float
    days_since_service: int
    failure_count: int
    corrective_repairs: int
    preventive_services: int

class AssetPredictiveHealthResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    asset_id: str
    asset_tag: str
    name: str
    category: str
    health_score: float
    risk_level: str
    risk_color: str
    failure_probability_30d: float
    metrics: AssetPredictiveHealthMetrics
    score_breakdown: Dict[str, Any]
    recommended_action: Union[str, Dict[str, Any]]
    location: Optional[str] = None

class FleetPredictiveOverviewSummary(BaseModel):
    model_config = ConfigDict(extra="allow")

    total_assets: int
    healthy_count: int
    attention_count: int
    high_risk_count: int
    upcoming_pm_count: int

class FleetPredictiveOverviewResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    summary: FleetPredictiveOverviewSummary
    high_risk_assets: List[AssetPredictiveHealthResponse] = []
    attention_required_assets: List[AssetPredictiveHealthResponse] = []
    healthy_assets: List[AssetPredictiveHealthResponse] = []
    upcoming_schedules: List[Dict[str, Any]] = []
