from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.approval import ApprovalRequest
from app.database.models.user import User
from app.schemas.approval import ApprovalDecisionRequest, ApprovalResponse
from app.services.approval_service import approval_service
from app.api.deps import require_role

router = APIRouter(prefix="/approvals", tags=["approvals"])

_approval_reader = require_role(["admin"])
_approval_decider = require_role(["admin"])

@router.get("", response_model=List[ApprovalResponse])
def list_approvals(
    status: Optional[str] = Query(None),
    limit: int = 50,
    current_user: User = Depends(_approval_reader),
    db: Session = Depends(get_db)
):
    q = db.query(ApprovalRequest)
    if status:
        q = q.filter(ApprovalRequest.status == status)
    return q.order_by(ApprovalRequest.created_at.desc()).limit(limit).all()

@router.post("/{approval_id}/decision", response_model=ApprovalResponse)
def decide_approval(
    approval_id: str,
    payload: ApprovalDecisionRequest,
    current_user: User = Depends(_approval_decider),
    db: Session = Depends(get_db)
):
    req = approval_service.decide_approval_request(
        db=db,
        approval_id=approval_id,
        approver_user=current_user,
        decision=payload.decision,
        decision_reason=payload.decision_reason
    )
    db.commit()
    db.refresh(req)
    return req

