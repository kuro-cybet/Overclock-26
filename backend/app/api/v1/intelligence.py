from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.explanation import DecisionExplanation
from app.services.intelligence_service import (
    historical_intelligence_service,
    predictive_alerts_service
)
from app.services.operational_intelligence_service import operational_intelligence_service
from app.database.models.user import User
from app.api.deps import require_role

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

_intel_admin = require_role(["admin"])
_intel_tech = require_role(["admin", "technician"])

@router.get("/historical-cases")
def get_similar_historical_cases(
    category: str = Query(...),
    symptoms: str = Query(...),
    room_id: Optional[str] = Query(None),
    current_user: User = Depends(_intel_tech),
    db: Session = Depends(get_db)
):
    """Retrieves verified similar past cases with diagnosis, parts used, and verified outcome."""
    return historical_intelligence_service.retrieve_similar_cases(
        db=db,
        category=category,
        symptom_text=symptoms,
        room_id=room_id
    )

@router.get("/predictive-alerts")
def get_predictive_alerts(
    current_user: User = Depends(_intel_admin),
    db: Session = Depends(get_db)
):
    """Surfaces evidence-based predictive operational alerts (SLA risks, parts depletion, readiness gaps)."""
    return predictive_alerts_service.evaluate_predictive_alerts(db=db)

@router.get("/operational-assessment")
def get_operational_assessment(
    current_user: User = Depends(_intel_admin),
    db: Session = Depends(get_db)
):
    """
    Holistic operational intelligence assessment across buildings, rooms,
    examinations, technician workloads, inventory, and SLAs.
    """
    return operational_intelligence_service.get_full_operational_assessment(db=db)

@router.get("/building-clusters")
def get_building_clusters(
    current_user: User = Depends(_intel_admin),
    db: Session = Depends(get_db)
):
    """Surfaces buildings experiencing multi-incident clusters."""
    return operational_intelligence_service.detect_building_incident_clusters(db=db)

@router.get("/rooms-at-risk")
def get_rooms_at_risk(
    current_user: User = Depends(_intel_admin),
    db: Session = Depends(get_db)
):
    """Surfaces rooms with unresolved maintenance or open work orders with scheduled bookings."""
    return operational_intelligence_service.detect_rooms_at_risk(db=db)

@router.get("/affected-examinations")
def get_affected_examinations(
    current_user: User = Depends(_intel_admin),
    db: Session = Depends(get_db)
):
    """Pinpoints upcoming examinations compromised by facility or equipment faults."""
    return operational_intelligence_service.detect_affected_examinations(db=db)

@router.get("/explanations")
def get_decision_explanations(
    decision_type: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(_intel_admin),
    db: Session = Depends(get_db)
):
    """Retrieves transparent decision explanation records for algorithmic choices."""
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
