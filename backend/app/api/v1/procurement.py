from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.approval import ProcurementRequest, ApprovalRequest
from app.database.models.inventory import InventoryItem
from app.database.models.user import User
from app.schemas.inventory import ProcurementCreateRequest
from app.api.deps import get_current_user

router = APIRouter(prefix="/procurement", tags=["procurement"])

@router.get("")
def list_procurement_requests(db: Session = Depends(get_db)):
    return db.query(ProcurementRequest).order_by(ProcurementRequest.created_at.desc()).all()

@router.post("")
def create_procurement_request(
    payload: ProcurementCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = db.query(InventoryItem).filter(InventoryItem.id == payload.item_id).first()
    cost = (item.unit_cost if item else 100.0) * payload.quantity

    count = db.query(ProcurementRequest).count()
    proc = ProcurementRequest(
        request_code=f"PRQ-{datetime.utcnow().strftime('%Y%m')}-{count + 1:04d}",
        item_id=payload.item_id,
        quantity=payload.quantity,
        estimated_cost=cost,
        work_order_id=payload.work_order_id,
        requester_id=current_user.id,
        status="requested"
    )
    db.add(proc)
    db.flush()

    # Create associated approval request
    app_req = ApprovalRequest(
        approval_type="purchase",
        target_entity_type="procurement",
        target_entity_id=proc.id,
        requester_id=current_user.id,
        status="pending",
        cost_amount=cost,
        justification=payload.justification or f"Procurement request for {payload.quantity}x {item.name if item else 'items'}."
    )
    db.add(app_req)
    db.commit()
    db.refresh(proc)
    return {
        "procurement_request": proc,
        "approval_request_id": app_req.id
    }

