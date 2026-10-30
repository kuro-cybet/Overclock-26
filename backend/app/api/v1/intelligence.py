from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.intelligence_service import (
    historical_intelligence_service,
    predictive_alerts_service
)

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

@router.get("/historical-cases")
def get_similar_historical_cases(
    category: str = Query(...),
    symptoms: str = Query(...),
    room_id: Optional[str] = Query(None),
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
def get_predictive_alerts(db: Session = Depends(get_db)):
    """Surfaces evidence-based predictive operational alerts (SLA risks, parts depletion, readiness gaps)."""
    return predictive_alerts_service.evaluate_predictive_alerts(db=db)

