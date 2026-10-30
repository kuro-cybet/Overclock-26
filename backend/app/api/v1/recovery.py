from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.user import User
from app.database.models.recovery import RecoveryExecution, RecoveryAction
from app.schemas.recovery import (
    RecoveryPlanRequest,
    RecoveryPlanResponse,
    RecoveryExecuteRequest,
    RecoveryInitiateRequest
)
from app.services.recovery_service import recovery_service
from app.services.recovery_execution_service import recovery_execution_service
from app.services.recovery_verification_service import recovery_verification_service
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

@router.post("/initiate")
def initiate_autonomous_recovery(
    payload: RecoveryInitiateRequest,
    current_user: User = Depends(_recovery_guard),
    db: Session = Depends(get_db)
):
    """
    Stages an end-to-end 13-step autonomous recovery execution plan.
    """
    execution = recovery_execution_service.initiate_recovery(
        db=db,
        incident_id=payload.incident_id,
        disruption_type=payload.disruption_type,
        chosen_plan_id=payload.chosen_plan_id,
        actions_spec=payload.actions,
        initiated_by_user=current_user
    )
    return {
        "execution_id": execution.id,
        "disruption_type": execution.disruption_type,
        "chosen_plan_id": execution.chosen_plan_id,
        "status": execution.status,
        "verification_status": execution.verification_status
    }

@router.post("/{execution_id}/run-actions")
def run_recovery_actions(
    execution_id: str,
    current_user: User = Depends(_recovery_guard),
    db: Session = Depends(get_db)
):
    """Executes staged recovery actions (room relocation, dispatch rebalance, notifications)."""
    return recovery_execution_service.execute_recovery_actions(
        db=db,
        execution_id=execution_id,
        operator=current_user
    )

@router.post("/{execution_id}/verify")
def verify_recovery_outcome(
    execution_id: str,
    current_user: User = Depends(_recovery_guard),
    db: Session = Depends(get_db)
):
    """
    Performs independent physical verification before marking recovery or incident as resolved.
    """
    return recovery_verification_service.verify_recovery_execution(
        db=db,
        execution_id=execution_id,
        inspector_user=current_user
    )

@router.get("/executions")
def list_recovery_executions(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Lists recovery execution audit records with verification status."""
    executions = db.query(RecoveryExecution).order_by(RecoveryExecution.created_at.desc()).limit(limit).all()
    results = []
    for ex in executions:
        actions = db.query(RecoveryAction).filter(RecoveryAction.execution_id == ex.id).all()
        results.append({
            "id": ex.id,
            "incident_id": ex.incident_id,
            "disruption_type": ex.disruption_type,
            "chosen_plan_id": ex.chosen_plan_id,
            "status": ex.status,
            "verification_status": ex.verification_status,
            "verification_outcome": ex.verification_outcome,
            "verified_at": ex.verified_at.isoformat() if ex.verified_at else None,
            "created_at": ex.created_at.isoformat() if ex.created_at else None,
            "actions_count": len(actions)
        })
    return results
