from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.incident import Incident
from app.database.models.report import Report
from app.database.models.work_order import WorkOrder
from app.database.models.user import User
from app.schemas.incident import (
    IncidentCreate,
    IncidentCorrelateRequest,
    IncidentResponse,
    IncidentDetailsResponse
)
from app.services.correlation_service import correlation_service
from app.services.sla_service import sla_service
from app.core.exceptions import EntityNotFoundError
from app.api.deps import get_current_user

router = APIRouter(prefix="/incidents", tags=["incidents"])

@router.get(
    "",
    response_model=List[IncidentResponse],
    summary="List Campus Incidents",
    description="Retrieves operational incidents across university buildings with multi-parameter filtering."
)
def list_incidents(
    status: Optional[str] = Query(None, description="Filter by lifecycle status: `open`, `in_progress`, `pending_parts`, `resolved`, `closed`"),
    severity: Optional[str] = Query(None, description="Filter by severity level: `low`, `medium`, `high`, `critical`"),
    category: Optional[str] = Query(None, description="Filter by operational category: `electrical`, `hvac`, `plumbing`, `network`, `av_equipment`, etc."),
    building_id: Optional[str] = Query(None, description="Filter by campus building UUID"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    db: Session = Depends(get_db)
):
    """
    List operational campus incidents with priority, SLA status, and correlation metadata.
    """
    q = db.query(Incident)
    if status:
        q = q.filter(Incident.status == status)
    if severity:
        q = q.filter(Incident.severity == severity)
    if category:
        q = q.filter(Incident.category == category)
    if building_id:
        q = q.filter(Incident.building_id == building_id)

    incidents = q.order_by(Incident.created_at.desc()).limit(limit).all()
    return incidents

@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get Incident by ID",
    description="Retrieves a single incident record by its unique UUID.",
    responses={
        404: {"description": "Incident not found"}
    }
)
def get_incident(
    incident_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve incident entity by ID.
    """
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise EntityNotFoundError("Incident", incident_id)
    return inc

@router.get(
    "/{incident_id}/details",
    response_model=IncidentDetailsResponse,
    summary="Get Detailed Incident Dossier",
    description="Retrieves incident record along with all correlated reports and associated work orders.",
    responses={
        404: {"description": "Incident not found"}
    }
)
def get_incident_details(
    incident_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve full incident dossier including linked reports and child work orders.
    """
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise EntityNotFoundError("Incident", incident_id)

    reports = db.query(Report).filter(Report.incident_id == incident_id).all()
    work_orders = db.query(WorkOrder).filter(WorkOrder.incident_id == incident_id).all()

    return {
        "incident": inc,
        "reports": reports,
        "work_orders": work_orders
    }

@router.post(
    "",
    response_model=IncidentResponse,
    summary="Create New Incident",
    description="Creates a new campus operational incident and automatically computes SLA resolution deadlines.",
    responses={
        401: {"description": "Authentication required"}
    }
)
def create_incident(
    payload: IncidentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register a new campus incident.
    """
    inc_count = db.query(Incident).count()
    sla_due = sla_service.calculate_deadline(payload.priority or "P3")

    incident = Incident(
        incident_code=f"INC-{datetime.utcnow().strftime('%Y%m')}-{inc_count + 1:04d}",
        title=payload.title,
        description=payload.description,
        category=payload.category,
        severity=payload.severity or "medium",
        priority=payload.priority or "P3",
        building_id=payload.building_id,
        room_id=payload.room_id,
        asset_id=payload.asset_id,
        status="open",
        sla_due_at=sla_due,
        is_sla_breached=False,
        correlated_count=1,
        summary=f"Incident registered by {current_user.name}."
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident

@router.post(
    "/correlate",
    response_model=IncidentResponse,
    summary="Correlate Reports into Incident",
    description="Aggregates multiple individual complaint reports into a single consolidated master incident.",
    responses={
        400: {"description": "Invalid correlation request"},
        401: {"description": "Authentication required"}
    }
)
def correlate_reports(
    payload: IncidentCorrelateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Correlate loose reports into a single canonical incident.
    """
    incident = correlation_service.correlate_reports_to_incident(
        db=db,
        report_ids=payload.report_ids,
        target_incident_id=payload.target_incident_id,
        canonical_title=payload.new_title,
        actor_id=current_user.id,
        actor_role=current_user.role
    )
    db.commit()
    db.refresh(incident)
    return incident
