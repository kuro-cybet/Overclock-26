from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.approval import ApprovalRequest
from app.database.models.user import User
from app.schemas.approval import ApprovalDecisionRequest, ApprovalResponse
from app.services.approval_service import approval_service
from app.api.deps import get_current_user

router = APIRouter(prefix="/approvals", tags=["approvals"])

@router.get(
    "",
    response_model=List[ApprovalResponse],
    summary="List Approval Requests",
    description="Retrieves administrative approval requests (purchase orders, costly repairs, technician reassignments, room overrides)."
)
def list_approvals(
    status: Optional[str] = Query(None, description="Filter by approval status: `pending`, `approved`, `rejected`"),
    limit: int = Query(50, ge=1, le=200, description="Maximum approval requests to return"),
    db: Session = Depends(get_db)
):
    """
    List approval requests ordered by creation timestamp.
    """
    q = db.query(ApprovalRequest)
    if status:
        q = q.filter(ApprovalRequest.status == status)
    return q.order_by(ApprovalRequest.created_at.desc()).limit(limit).all()

@router.post(
    "/{approval_id}/decision",
    response_model=ApprovalResponse,
    summary="Submit Approval Decision",
    description="Approves or rejects a pending request. Enforces strict separation of duties (requester cannot approve their own request) and role-based authority limits.",
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Separation of duties violation (cannot approve own request) or insufficient role authority"},
        404: {"description": "Approval request not found"}
    }
)
def decide_approval(
    approval_id: str,
    payload: ApprovalDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit decision on pending approval with governance and separation-of-duties checks.
    """
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
