from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class KPICards(BaseModel):
    open_incidents: int
    sla_compliance_rate: float
    active_work_orders: int
    room_utilisation_rate: float
    parts_shortages: int
    pending_approvals: Optional[int] = None

class AnalyticsDashboardResponse(BaseModel):
    kpi: KPICards
    incidents_by_category: Dict[str, int]
    incidents_by_severity: Dict[str, int]
    work_orders_by_status: Dict[str, int]
    room_readiness_breakdown: Dict[str, int]
    sla_monthly_trend: List[Dict[str, Any]]

class PortalDashboardResponse(BaseModel):
    portal: str
    kpi: Dict[str, Any]
    recent_incidents: Optional[List[Dict[str, Any]]] = None
    pending_approvals: Optional[List[Dict[str, Any]]] = None
    category_distribution: Optional[Dict[str, int]] = None
    sla_trend: Optional[List[Dict[str, Any]]] = None
    readiness_summary: Optional[Dict[str, int]] = None
    my_tasks: Optional[List[Dict[str, Any]]] = None
    active_task: Optional[Dict[str, Any]] = None
    shift: Optional[str] = None
    parts_shortages: Optional[int] = None
    timetable: Optional[List[Dict[str, Any]]] = None
    my_requests: Optional[List[Dict[str, Any]]] = None
    campus_incidents: Optional[List[Dict[str, Any]]] = None
