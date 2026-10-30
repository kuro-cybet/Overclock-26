from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.sla_service import sla_service

router = APIRouter(prefix="/sla", tags=["sla"])

@router.get("/status")
def get_sla_status(db: Session = Depends(get_db)):
    result = sla_service.evaluate_all_incidents_sla(db)
    db.commit()
    return result

