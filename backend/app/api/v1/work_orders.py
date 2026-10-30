import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status as http_status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.work_order import WorkOrder
from app.database.models.incident import Incident
from app.database.models.inventory import StockReservation
from app.database.models.approval import ApprovalRequest
from app.database.models.notification import Notification
from app.database.models.user import User
from app.schemas.work_order import (
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderReassignRequest,
    WorkOrderRequestReassignment,
    WorkOrderResponse
)
from app.services.assignment_service import assignment_service
from app.core.state_machine import validate_transition
from app.core.exceptions import EntityNotFoundError, CampusOpsException
from app.api.deps import get_current_user

router = APIRouter(prefix="/work-orders", tags=["work-orders"])

@router.get("", response_model=List[WorkOrderResponse])
def list_work_orders(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(WorkOrder)

    # Scoping: Technicians view only their assigned work orders by default
    if current_user.role == "technician":
        q = q.filter(WorkOrder.assigned_technician_id == current_user.id)

    if status:
        q = q.filter(WorkOrder.status == status)
    if priority:
        q = q.filter(WorkOrder.priority == priority)

    work_orders = q.order_by(WorkOrder.created_at.desc()).limit(limit).all()
    return work_orders

@router.get("/{work_order_id}", response_model=WorkOrderResponse)
def get_work_order(work_order_id: str, db: Session = Depends(get_db)):
    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not wo:
        raise EntityNotFoundError("WorkOrder", work_order_id)
    return wo

@router.get("/{work_order_id}/details")
def get_work_order_details(work_order_id: str, db: Session = Depends(get_db)):
    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not wo:
        raise EntityNotFoundError("WorkOrder", work_order_id)

    incident = db.query(Incident).filter(Incident.id == wo.incident_id).first()
    reservations = db.query(StockReservation).filter(StockReservation.work_order_id == wo.id).all()
    technician = db.query(User).filter(User.id == wo.assigned_technician_id).first() if wo.assigned_technician_id else None

    return {
        "work_order": wo,
        "incident": incident,
        "technician": technician,
        "reservations": reservations
    }

@router.post("", response_model=WorkOrderResponse)
def create_work_order(
    payload: WorkOrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    wo_count = db.query(WorkOrder).count()
    wo = WorkOrder(
        work_order_code=f"WO-{datetime.utcnow().strftime('%Y%m')}-{wo_count + 1:04d}",
        incident_id=payload.incident_id,
        title=payload.title,
        description=payload.description,
        assigned_technician_id=payload.assigned_technician_id,
        priority=payload.priority or "P3",
        status="assigned",
        required_skills=json.dumps(payload.required_skills or []),
        sla_deadline=payload.sla_deadline,
        checklist=json.dumps([
            {"task": "Site inspection & safety lock-out", "done": False},
            {"task": "Hardware diagnosis and fault isolation", "done": False},
            {"task": "Operational test & signoff", "done": False}
        ])
    )
    db.add(wo)
    db.commit()
    db.refresh(wo)
    return wo

@router.patch("/{work_order_id}", response_model=WorkOrderResponse)
def update_work_order(
    work_order_id: str,
    payload: WorkOrderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not wo:
        raise EntityNotFoundError("WorkOrder", work_order_id)

    # Validate state transition if status changed
    if payload.status and payload.status != wo.status:
        validate_transition("work_order", wo.status, payload.status)
        wo.status = payload.status
        if payload.status == "completed":
            wo.completed_at = datetime.utcnow()
            # If all work orders for incident are completed, mark incident resolved
            inc = db.query(Incident).filter(Incident.id == wo.incident_id).first()
            if inc:
                inc.status = "resolved"
                inc.resolved_at = datetime.utcnow()

    if payload.diagnosis is not None:
        wo.diagnosis = payload.diagnosis
    if payload.checklist is not None:
        wo.checklist = json.dumps(payload.checklist)
    if payload.evidence_notes is not None:
        wo.evidence_notes = payload.evidence_notes
    if payload.blocked_reason is not None:
        wo.blocked_reason = payload.blocked_reason

    db.commit()
    db.refresh(wo)
    return wo

@router.post("/{work_order_id}/reassign", response_model=WorkOrderResponse)
def reassign_work_order(
    work_order_id: str,
    payload: WorkOrderReassignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Technicians cannot directly reassign work orders; only request
    if current_user.role == "technician":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Technicians are not authorized to directly reassign work orders. They can only submit a reassignment request."
        )

    wo = assignment_service.assign_technician_to_work_order(
        db=db,
        work_order_id=work_order_id,
        technician_id=payload.new_technician_id,
        reassign_reason=payload.reassignment_reason
    )
    db.commit()
    db.refresh(wo)
    return wo

@router.post("/{work_order_id}/request-reassignment")
def request_reassignment(
    work_order_id: str,
    payload: WorkOrderRequestReassignment,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not wo:
        raise EntityNotFoundError("WorkOrder", work_order_id)

    # Technicians can only request reassignment for orders assigned to them
    if current_user.role == "technician" and wo.assigned_technician_id != current_user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="You can only request reassignment for work orders assigned to you."
        )

    # 1. Create an ApprovalRequest of type 'reassignment'
    approval = ApprovalRequest(
        approval_type="reassignment",
        target_entity_type="work_order",
        target_entity_id=wo.id,
        requester_id=current_user.id,
        justification=f"{payload.reason}" + (f" | Additional Notes: {payload.notes}" if payload.notes else ""),
        status="pending"
    )
    db.add(approval)

    # 2. Issue targeted supervisory notification
    notif = Notification(
        recipient_id="admin",
        recipient_role="admin",
        title=f"Reassignment Requested: {wo.work_order_code}",
        message=f"Technician {current_user.name} submitted a reassignment request for '{wo.title}'. Reason: {payload.reason}",
        type="action_required",
        link_url="/admin/work-orders"
    )
    db.add(notif)

    # 3. Log into work order evidence notes
    timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    req_tag = f"\n[Reassignment Requested by {current_user.name} ({timestamp_str}) — Reason: {payload.reason}]"
    wo.evidence_notes = (wo.evidence_notes or "") + req_tag

    db.commit()
    return {
        "status": "requested",
        "work_order_id": wo.id,
        "approval_id": approval.id,
        "message": f"Reassignment request submitted to dispatch supervisor for work order {wo.work_order_code}."
    }

