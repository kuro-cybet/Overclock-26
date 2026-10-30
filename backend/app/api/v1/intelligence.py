from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.explanation import DecisionExplanation
from app.services.intelligence_service import (
    historical_intelligence_service,
    predictive_alerts_service
)
from app.services.operational_intelligence_service import operational_intelligence_service
from app.schemas.intelligence import (
    HistoricalCaseResponse,
    PredictiveAlertResponse,
    BuildingClusterResponse,
    RoomAtRiskResponse,
    AffectedExaminationResponse,
    DecisionExplanationResponse,
    OperationalAssessmentResponse
)

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

@router.get(
    "/historical-cases",
    response_model=List[HistoricalCaseResponse],
    summary="Retrieve Similar Historical Cases",
    description="Retrieves verified similar past cases with diagnosis, parts used, root cause analysis, and verified outcome."
)
def get_similar_historical_cases(
    category: str = Query(..., description="Operational fault category: `electrical`, `hvac`, `network`, `plumbing`, etc."),
    symptoms: str = Query(..., description="Text description of symptoms or error observations"),
    room_id: Optional[str] = Query(None, description="Optional room UUID for location-specific historical matching"),
    db: Session = Depends(get_db)
):
    """
    Search historical resolution repository for similar past equipment incidents.
    """
    return historical_intelligence_service.retrieve_similar_cases(
        db=db,
        category=category,
        symptom_text=symptoms,
        room_id=room_id
    )

@router.get(
    "/predictive-alerts",
    response_model=List[PredictiveAlertResponse],
    summary="Get Predictive Operational Alerts",
    description="Surfaces evidence-based predictive operational alerts (approaching SLA risks, parts depletion, examination readiness gaps)."
)
def get_predictive_alerts(db: Session = Depends(get_db)):
    """
    Evaluate multi-factor predictive operational alerts.
    """
    return predictive_alerts_service.evaluate_predictive_alerts(db=db)

@router.get(
    "/operational-assessment",
    response_model=OperationalAssessmentResponse,
    summary="Get Holistic Operational Assessment",
    description="Holistic operational intelligence assessment across buildings, rooms, examinations, technician workloads, inventory, and SLAs."
)
def get_operational_assessment(db: Session = Depends(get_db)):
    """
    Perform full synthesized multi-dimensional campus operational risk assessment.
    """
    return operational_intelligence_service.get_full_operational_assessment(db=db)

@router.get(
    "/building-clusters",
    response_model=List[BuildingClusterResponse],
    summary="Detect Multi-Incident Building Clusters",
    description="Identifies buildings experiencing concurrent multi-incident clusters that signal potential systemic infrastructure failures."
)
def get_building_clusters(db: Session = Depends(get_db)):
    """
    Surfaces buildings experiencing multi-incident clusters.
    """
    return operational_intelligence_service.detect_building_incident_clusters(db=db)

@router.get(
    "/rooms-at-risk",
    response_model=List[RoomAtRiskResponse],
    summary="Detect High-Risk Rooms",
    description="Surfaces rooms with unresolved maintenance or open work orders that have scheduled immediate academic bookings."
)
def get_rooms_at_risk(db: Session = Depends(get_db)):
    """
    Surfaces rooms with unresolved maintenance or open work orders with scheduled bookings.
    """
    return operational_intelligence_service.detect_rooms_at_risk(db=db)

@router.get(
    "/affected-examinations",
    response_model=List[AffectedExaminationResponse],
    summary="Pinpoint Jeopardized Examination Sessions",
    description="Pinpoints upcoming examinations compromised by facility, HVAC, or equipment faults, providing contingency recommendations."
)
def get_affected_examinations(db: Session = Depends(get_db)):
    """
    Pinpoints upcoming examinations compromised by facility or equipment faults.
    """
    return operational_intelligence_service.detect_affected_examinations(db=db)

@router.get(
    "/explanations",
    response_model=List[DecisionExplanationResponse],
    summary="Get Algorithmic Decision Explanations",
    description="Retrieves transparent decision explanation records detailing why specific algorithmic routing or recovery actions were chosen."
)
def get_decision_explanations(
    decision_type: Optional[str] = Query(None, description="Filter by decision type: `technician_assignment`, `recovery_plan`, `priority_scoring`"),
    limit: int = Query(20, ge=1, le=100, description="Maximum explanation records to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieves transparent decision explanation records for algorithmic choices.
    """
    query = db.query(DecisionExplanation)
    if decision_type:
        query = query.filter(DecisionExplanation.decision_type == decision_type)
    records = query.order_by(DecisionExplanation.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "decision_type": r.decision_type,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "chosen_option": r.chosen_option,
            "explanation_text": r.explanation_text,
            "confidence_score": r.confidence_score,
            "factors": r.factors_json,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in records
    ]
