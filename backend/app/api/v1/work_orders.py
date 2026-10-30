import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status as http_status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.work_order import WorkOrder
from app.database.models.incident import Incident
from app.database.models.inventory import StockReservation, InventoryItem
from app.database.models.approval import ApprovalRequest, ProcurementRequest
from app.database.models.notification import Notification
from app.database.models.user import User
from app.database.models.work_order_checklist import WorkOrderChecklistItem
from app.database.models.inventory_transaction import InventoryTransaction
from app.schemas.work_order import (
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderReassignRequest,
    WorkOrderRequestReassignment,
    WorkOrderResponse,
    ChecklistItemResponse,
    ChecklistItemUpdate,
    PartsRequisitionRequest
)
from app.services.assignment_service import assignment_service
from app.services.inventory_service import inventory_service
from app.services.event_service import event_service
from app.core.state_machine import validate_transition
from app.core.exceptions import EntityNotFoundError, CampusOpsException, StockUnavailableError
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
    checklists = db.query(WorkOrderChecklistItem).filter(WorkOrderChecklistItem.work_order_id == wo.id).order_by(WorkOrderChecklistItem.step_order.asc()).all()

    return {
        "work_order": wo,
        "incident": incident,
        "technician": technician,
        "reservations": reservations,
        "checklists": checklists
    }

@router.get("/{work_order_id}/checklist", response_model=List[ChecklistItemResponse])
def get_work_order_checklist(
    work_order_id: str,
    db: Session = Depends(get_db)
):
    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not wo:
        raise EntityNotFoundError("WorkOrder", work_order_id)

    items = (
        db.query(WorkOrderChecklistItem)
        .filter(WorkOrderChecklistItem.work_order_id == work_order_id)
        .order_by(WorkOrderChecklistItem.step_order.asc())
        .all()
    )

    # Auto-seed default items if none exist yet for this work order
    if not items:
        default_tasks = [
            "Site physical inspection & safety power lock-out",
            "Hardware diagnostic scan and fault component isolation",
            "Functional load testing and operational verification signoff"
        ]
        created_items = []
        for idx, task in enumerate(default_tasks):
            ci = WorkOrderChecklistItem(
                work_order_id=wo.id,
                task_description=task,
                step_order=idx + 1,
                is_completed=False,
                verification_status="pending"
            )
            db.add(ci)
            created_items.append(ci)
        db.commit()
        items = created_items

    return items

@router.patch("/{work_order_id}/checklist/{item_id}", response_model=ChecklistItemResponse)
def update_checklist_item(
    work_order_id: str,
    item_id: str,
    payload: ChecklistItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = (
        db.query(WorkOrderChecklistItem)
        .filter(WorkOrderChecklistItem.id == item_id, WorkOrderChecklistItem.work_order_id == work_order_id)
        .first()
    )
    if not item:
        raise EntityNotFoundError("WorkOrderChecklistItem", item_id)

    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not wo:
        raise EntityNotFoundError("WorkOrder", work_order_id)

    # Technician can only update checklist for work orders assigned to them (or admin)
    if current_user.role == "technician" and wo.assigned_technician_id != current_user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="You can only update checklist items for tasks assigned to you."
        )

    item.is_completed = payload.is_completed
    item.completed_at = datetime.utcnow() if payload.is_completed else None
    item.completed_by_id = current_user.id if payload.is_completed else None
    if payload.verification_notes is not None:
        item.verification_notes = payload.verification_notes
    item.verification_status = "verified" if payload.is_completed else "pending"

    # Also synchronize wo.checklist JSON string
    all_items = (
        db.query(WorkOrderChecklistItem)
        .filter(WorkOrderChecklistItem.work_order_id == work_order_id)
        .order_by(WorkOrderChecklistItem.step_order.asc())
        .all()
    )
    checklist_json = [{"task": it.task_description, "done": it.is_completed} for it in all_items]
    wo.checklist = json.dumps(checklist_json)

    event_service.log_event(
        db=db,
        event_type="checklist_updated",
        entity_type="work_order",
        entity_id=work_order_id,
        severity="info",
        payload={
            "step_order": item.step_order,
            "task": item.task_description,
            "is_completed": item.is_completed
        },
        actor_id=current_user.id
    )

    db.commit()
    db.refresh(item)
    return item

@router.post("/{work_order_id}/parts-requisition")
def requisition_parts(
    work_order_id: str,
    payload: PartsRequisitionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not wo:
        raise EntityNotFoundError("WorkOrder", work_order_id)

    # Validate technician assignment
    if current_user.role == "technician" and wo.assigned_technician_id != current_user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="You can only request parts for work orders assigned to your shift profile."
        )

    item = db.query(InventoryItem).filter(InventoryItem.id == payload.item_id).first()
    if not item:
        raise EntityNotFoundError("InventoryItem", payload.item_id)

    available = max(0, (item.stock_quantity or 0) - (item.reserved_quantity or 0))

    if available >= payload.quantity:
        # Stock available: Reserve it transactionally without decreasing total stock
        res = inventory_service.reserve_stock(
            db=db,
            work_order_id=wo.id,
            item_id=item.id,
            quantity=payload.quantity
        )

        # Record in inventory transactions ledger
        tx = InventoryTransaction(
            item_id=item.id,
            work_order_id=wo.id,
            actor_id=current_user.id,
            transaction_type="reservation_hold",
            quantity=payload.quantity,
            notes=f"Reserved for {wo.work_order_code}: {payload.justification or 'Technician field demand'}"
        )
        db.add(tx)
        db.commit()

        return {
            "status": "reserved",
            "type": "reservation",
            "item_name": item.name,
            "quantity": payload.quantity,
            "reservation_id": res.id,
            "work_order_id": wo.id,
            "message": f"Successfully reserved {payload.quantity}x '{item.name}'. Available on site for dispatch."
        }
    else:
        # Stock depleted: Create ProcurementRequest + purchase ApprovalRequest, flag order blocked
        count = db.query(ProcurementRequest).count()
        cost = float(item.unit_cost or 50.0) * payload.quantity
        proc = ProcurementRequest(
            request_code=f"PRQ-{datetime.utcnow().strftime('%Y%m')}-{count + 1:04d}",
            item_id=item.id,
            quantity=payload.quantity,
            estimated_cost=cost,
            work_order_id=wo.id,
            requester_id=current_user.id,
            status="requested"
        )
        db.add(proc)
        db.flush()

        app_req = ApprovalRequest(
            approval_type="purchase",
            target_entity_type="procurement",
            target_entity_id=proc.id,
            requester_id=current_user.id,
            cost_amount=cost,
            justification=f"Spare part depletion on {wo.work_order_code}: {payload.quantity}x {item.name}. {payload.justification or ''}",
            status="pending"
        )
        db.add(app_req)

        # Transition work order to blocked
        wo.status = "blocked"
        wo.blocked_reason = f"Spare part depleted: Awaiting procurement of {payload.quantity}x {item.name}"

        # Record transaction log
        tx = InventoryTransaction(
            item_id=item.id,
            work_order_id=wo.id,
            actor_id=current_user.id,
            transaction_type="procurement_request",
            quantity=payload.quantity,
            notes=f"Out of stock ({available} available). Staged procurement request {proc.request_code}."
        )
        db.add(tx)
        db.commit()

        return {
            "status": "blocked_awaiting_procurement",
            "type": "procurement",
            "item_name": item.name,
            "quantity": payload.quantity,
            "work_order_id": wo.id,
            "procurement_id": proc.id,
            "approval_id": app_req.id,
            "message": f"Insufficient stock ({available} available). Emergency procurement staged and {wo.work_order_code} flagged as blocked."
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
            {"task": "Site physical inspection & safety power lock-out", "done": False},
            {"task": "Hardware diagnostic scan and fault component isolation", "done": False},
            {"task": "Functional load testing and operational verification signoff", "done": False}
        ])
    )
    db.add(wo)
    db.flush()

    # Create persistent WorkOrderChecklistItem rows
    default_tasks = [
        "Site physical inspection & safety power lock-out",
        "Hardware diagnostic scan and fault component isolation",
        "Functional load testing and operational verification signoff"
    ]
    for idx, task in enumerate(default_tasks):
        ci = WorkOrderChecklistItem(
            work_order_id=wo.id,
            task_description=task,
            step_order=idx + 1,
            is_completed=False,
            verification_status="pending"
        )
        db.add(ci)

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

        # Enforce checklist completion before marking 'completed'
        if payload.status == "completed":
            checklist_items = (
                db.query(WorkOrderChecklistItem)
                .filter(WorkOrderChecklistItem.work_order_id == wo.id)
                .all()
            )
            if checklist_items:
                incomplete = [item.task_description for item in checklist_items if not item.is_completed]
                if incomplete:
                    raise HTTPException(
                        status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=(
                            f"Cannot complete work order {wo.work_order_code}: "
                            f"{len(incomplete)} mandatory checklist step(s) remain incomplete: "
                            f"{', '.join(incomplete[:2])}"
                        )
                    )

            wo.completed_at = datetime.utcnow()
            # If all work orders for incident are completed, mark incident resolved
            inc = db.query(Incident).filter(Incident.id == wo.incident_id).first()
            if inc:
                inc.status = "resolved"
                inc.resolved_at = datetime.utcnow()

        wo.status = payload.status

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
