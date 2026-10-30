from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.user import User
from app.database.models.recovery import RecoveryExecution, RecoveryAction
from app.schemas.recovery import (
    RecoveryPlanRequest,
    RecoveryPlanResponse,
    RecoveryExecuteRequest,
    RecoveryExecuteResponse,
    RecoveryInitiateRequest,
    RecoveryInitiateResponse,
    RecoveryRunActionsResponse,
    RecoveryVerifyResponse,
    RecoveryExecutionSummary
)
from app.services.recovery_service import recovery_service
from app.services.recovery_execution_service import recovery_execution_service
from app.services.recovery_verification_service import recovery_verification_service
from app.api.deps import require_admin_sub_role

router = APIRouter(prefix="/recovery", tags=["recovery"])

# Recovery actions restricted to system_admin and facilities_admin
_recovery_guard = require_admin_sub_role(["system_admin", "facilities_admin"])

@router.post(
    "/plan",
    response_model=RecoveryPlanResponse,
    summary="Generate Autonomous Recovery Plan",
    description="Synthesizes viable recovery options for operational disruptions (exam room failures, technician absences, critical parts shortages, network outages).",
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin sub-role required (system_admin or facilities_admin)"}
    }
)
def get_recovery_plan(
    payload: RecoveryPlanRequest,
    current_user: User = Depends(_recovery_guard),
    db: Session = Depends(get_db)
):
    """
    Generate scored recovery plan options based on constraint solving.
    """
    plan = recovery_service.generate_recovery_plan(
        db=db,
        disruption_type=payload.disruption_type,
        entity_id=payload.entity_id
    )
    return plan

@router.post(
    "/execute",
    response_model=RecoveryExecuteResponse,
    summary="Execute Single Recovery Action",
    description="Executes a targeted recovery action (room relocation, work order reassignment, procurement staging) with real-time pre-execution revalidation.",
    responses={
        400: {"description": "Unknown recovery action"},
        401: {"description": "Authentication required"},
        403: {"description": "Admin sub-role required"},
        404: {"description": "Target entity not found"},
        409: {"description": "Pre-execution revalidation failed (destination room occupied or staff unavailable)"}
    }
)
def execute_recovery(
    payload: RecoveryExecuteRequest,
    current_user: User = Depends(_recovery_guard),
    db: Session = Depends(get_db)
):
    """
    Execute selected recovery plan option with just-in-time state revalidation.
    """
    payload_dict = payload.action_payload.model_dump() if hasattr(payload.action_payload, "model_dump") else payload.action_payload
    res = recovery_service.execute_recovery_plan(
        db=db,
        target_action=payload.target_action,
        action_payload=payload_dict,
        actor_id=current_user.id,
        actor_role=current_user.role,
        approval_override=payload.approval_override
    )
    db.commit()
    return res

@router.post(
    "/initiate",
    response_model=RecoveryInitiateResponse,
    summary="Stage Multi-Step Autonomous Recovery Execution",
    description="Stages an end-to-end multi-step autonomous recovery execution plan with staged actions awaiting execution and independent physical verification.",
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin sub-role required"}
    }
)
def initiate_autonomous_recovery(
    payload: RecoveryInitiateRequest,
    current_user: User = Depends(_recovery_guard),
    db: Session = Depends(get_db)
):
    """
    Stages an end-to-end autonomous recovery execution plan.
    """
    raw_actions = [
        a.model_dump() if hasattr(a, "model_dump") else a
        for a in payload.actions
    ]
    execution = recovery_execution_service.initiate_recovery(
        db=db,
        incident_id=payload.incident_id,
        disruption_type=payload.disruption_type,
        chosen_plan_id=payload.chosen_plan_id,
        actions_spec=raw_actions,
        initiated_by_user=current_user
    )
    return {
        "execution_id": execution.id,
        "disruption_type": execution.disruption_type,
        "chosen_plan_id": execution.chosen_plan_id,
        "status": execution.status,
        "verification_status": execution.verification_status
    }

@router.post(
    "/{execution_id}/run-actions",
    response_model=RecoveryRunActionsResponse,
    summary="Run Staged Recovery Actions",
    description="Executes staged recovery actions (room relocation, technician dispatch rebalance, notification broadcasts) for an initiated recovery execution.",
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin sub-role required"},
        404: {"description": "Recovery execution not found"}
    }
)
def run_recovery_actions(
    execution_id: str,
    current_user: User = Depends(_recovery_guard),
    db: Session = Depends(get_db)
):
    """
    Executes staged recovery actions (room relocation, dispatch rebalance, notifications).
    """
    return recovery_execution_service.execute_recovery_actions(
        db=db,
        execution_id=execution_id,
        operator=current_user
    )

@router.post(
    "/{execution_id}/verify",
    response_model=RecoveryVerifyResponse,
    summary="Perform Independent Physical Verification",
    description="Conducts post-execution verification checks before allowing an incident or recovery state to be marked as resolved.",
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin sub-role required"},
        404: {"description": "Recovery execution not found"}
    }
)
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

@router.get(
    "/executions",
    response_model=List[RecoveryExecutionSummary],
    summary="List Recovery Execution Audits",
    description="Retrieves recovery execution audit records with status, verification outcomes, and timestamp history."
)
def list_recovery_executions(
    limit: int = 20,
    current_user: User = Depends(_recovery_guard),
    db: Session = Depends(get_db)
):
    """
    Lists recovery execution audit records with verification status.
    """
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
