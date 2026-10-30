from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.sla_service import sla_service
from app.schemas.sla import SlaStatusResponse

router = APIRouter(prefix="/sla", tags=["sla"])

@router.get(
    "/status",
    response_model=SlaStatusResponse,
    summary="Evaluate Real-Time SLA Status",
    description="Evaluates all active campus incidents against resolution SLA deadlines, triggering automated escalation notifications for breached or approaching targets."
)
def get_sla_status(db: Session = Depends(get_db)):
    """
    Evaluate SLA compliance across all open and in-progress incidents.
    """
    result = sla_service.evaluate_all_incidents_sla(db)
    db.commit()
    return result
