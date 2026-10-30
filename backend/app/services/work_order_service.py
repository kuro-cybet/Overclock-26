"""Work-order creation shared by triage automation and the admin API.

A work order starts as ``unassigned``.  When a technician is supplied it is
dispatched immediately; otherwise the assignment service scores the available
technicians and picks the best match.  If dispatch cannot find anyone the order
stays unassigned and the facilities desk gets an in-app alert.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import CampusOpsException
from app.database.models.incident import Incident
from app.database.models.user import User
from app.database.models.work_order import WorkOrder
from app.database.models.work_order_checklist import WorkOrderChecklistItem
from app.services import workflow_notifications
from app.services.assignment_service import assignment_service

logger = logging.getLogger(__name__)

DEFAULT_CHECKLIST = [
    "Site physical inspection & safety power lock-out",
    "Hardware diagnostic scan and fault component isolation",
    "Functional load testing and operational verification signoff",
]

# Category -> technician skills.  Matching uses "any of", so one hit is enough.
CATEGORY_SKILLS = {
    "network": ["network", "wifi", "cabling", "router_config"],
    "wifi": ["wifi", "network"],
    "electrical": ["electrical", "power_distribution"],
    "hvac": ["hvac"],
    "plumbing": ["plumbing", "water_systems", "sanitary_maintenance"],
    "cleanliness": ["general_cleaning", "sanitation", "waste_management"],
    "safety": ["electrical", "hardware"],
    "equipment": ["hardware", "av_equipment"],
    "classroom": ["classroom_readiness", "av_equipment", "exam_setup"],
}


def skills_for_category(category: Optional[str]) -> List[str]:
    return CATEGORY_SKILLS.get((category or "").lower(), ["hardware"])


def _next_code(db: Session) -> str:
    count = db.query(WorkOrder).count()
    return f"WO-{datetime.utcnow().strftime('%Y%m')}-{count + 1:04d}"


def _technician(db: Session, user_id: Optional[str]) -> Optional[User]:
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def create_work_order_for_incident(
    db: Session,
    incident: Incident,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_technician_id: Optional[str] = None,
    required_skills: Optional[List[str]] = None,
    sla_deadline=None,
    auto_assign: bool = True,
    actor_id: Optional[str] = None,
) -> Tuple[WorkOrder, Optional[User]]:
    work_order = WorkOrder(
        work_order_code=_next_code(db),
        incident_id=incident.id,
        title=title or f"Repair: {incident.title}",
        description=description
        or (
            f"Auto-generated from {incident.incident_code}. "
            f"{incident.description}"
        ),
        assigned_technician_id=None,
        priority=priority or incident.priority or "P3",
        status="unassigned",
        required_skills=json.dumps(
            required_skills
            if required_skills is not None
            else skills_for_category(incident.category)
        ),
        sla_deadline=sla_deadline or incident.sla_due_at,
        checklist=json.dumps([{"task": task, "done": False} for task in DEFAULT_CHECKLIST]),
    )
    db.add(work_order)
    db.flush()

    for index, task in enumerate(DEFAULT_CHECKLIST, start=1):
        db.add(
            WorkOrderChecklistItem(
                work_order_id=work_order.id,
                task_description=task,
                step_order=index,
                is_completed=False,
                verification_status="pending",
            )
        )
    db.flush()

    technician: Optional[User] = None

    if assigned_technician_id:
        work_order = assignment_service.assign_technician_to_work_order(
            db,
            work_order_id=work_order.id,
            technician_id=assigned_technician_id,
        )
        technician = _technician(db, work_order.assigned_technician_id)
    elif auto_assign:
        try:
            work_order = assignment_service.assign_technician_to_work_order(
                db,
                work_order_id=work_order.id,
            )
            technician = _technician(db, work_order.assigned_technician_id)
        except CampusOpsException as exc:
            logger.warning(
                "[WorkOrder] Auto-dispatch failed for %s: %s",
                work_order.work_order_code,
                exc.detail,
            )
            workflow_notifications.work_order_unassigned(
                db, work_order, incident, reason=str(exc.detail)
            )

    db.flush()
    return work_order, technician


def ensure_work_order_for_incident(
    db: Session,
    incident: Incident,
    *,
    actor_id: Optional[str] = None,
    auto_assign: bool = True,
) -> Tuple[WorkOrder, Optional[User]]:
    """Return the incident's work order, creating and dispatching one if needed."""
    existing = (
        db.query(WorkOrder)
        .filter(WorkOrder.incident_id == incident.id)
        .order_by(WorkOrder.created_at.asc())
        .first()
    )
    if existing:
        if not existing.assigned_technician_id and auto_assign:
            try:
                existing = assignment_service.assign_technician_to_work_order(
                    db,
                    work_order_id=existing.id,
                )
            except CampusOpsException as exc:
                logger.warning(
                    "[WorkOrder] Auto-dispatch retry failed for %s: %s",
                    existing.work_order_code,
                    exc.detail,
                )
                workflow_notifications.work_order_unassigned(
                    db, existing, incident, reason=str(exc.detail)
                )
        return existing, _technician(db, existing.assigned_technician_id)

    return create_work_order_for_incident(
        db,
        incident,
        auto_assign=auto_assign,
        actor_id=actor_id,
    )
