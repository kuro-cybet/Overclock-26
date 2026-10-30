from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.user import User
from app.schemas.recovery import RecoveryPlanRequest, RecoveryPlanResponse, RecoveryExecuteRequest
from app.services.recovery_service import recovery_service
from app.api.deps import require_admin_sub_role

router = APIRouter(prefix="/recovery", tags=["recovery"])

# Recovery actions restricted to system_admin and facilities_admin
_recovery_guard = require_admin_sub_role(["system_admin", "facilities_admin"])

@router.post("/plan", response_model=RecoveryPlanResponse)
def get_recovery_plan(
    payload: RecoveryPlanRequest,
    current_user: User = Depends(_recovery_guard),
    db: Session = Depends(get_db)
):
    plan = recovery_service.generate_recovery_plan(
        db=db,
        disruption_type=payload.disruption_type,
        entity_id=payload.entity_id
    )
    return plan

@router.post("/execute")
def execute_recovery(
    payload: RecoveryExecuteRequest,
    current_user: User = Depends(_recovery_guard),
    db: Session = Depends(get_db)
):
    res = recovery_service.execute_recovery_plan(
        db=db,
        target_action=payload.target_action,
        action_payload=payload.action_payload,
        actor_id=current_user.id,
        actor_role=current_user.role,
        approval_override=payload.approval_override
    )
    db.commit()
    return res

