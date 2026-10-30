from typing import Dict, Any, List
from pydantic import BaseModel

class KPICards(BaseModel):
    open_incidents: int
    sla_compliance_rate: float
    active_work_orders: int
    room_utilisation_rate: float
    parts_shortages: int

class AnalyticsSummary(BaseModel):
    kpi: KPICards
    incidents_by_category: Dict[str, int]
    incidents_by_severity: Dict[str, int]
    work_orders_by_status: Dict[str, int]
    room_readiness_breakdown: Dict[str, int]
    sla_monthly_trend: List[Dict[str, Any]]

