from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.user import User
from app.services.sla_service import sla_service
from app.api.deps import require_role

router = APIRouter(prefix="/sla", tags=["sla"])


@router.get("/status")
def get_sla_status(
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    result = sla_service.evaluate_all_incidents_sla(db)
    db.commit()
    return result
