"""Lifecycle notifications: in-app alerts plus queued email for each hand-off.

Callers (intake, correlation, assignment, work-order API) call these helpers at
the moment a workflow event happens.  The helpers only add rows and flush; the
owning endpoint/service commits the transaction.
"""

import json
import logging
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.config import settings
from app.database.models.campus import Building
from app.database.models.incident import Incident
from app.database.models.report import Report
from app.database.models.room import Room
from app.database.models.user import User
from app.database.models.work_order import WorkOrder
from app.services import email_templates
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

_REPORTER_LINKS = {
    "student": "/student/requests",
    "faculty": "/faculty/requests",
    "admin": "/admin/incidents",
    "technician": "/technician/tasks",
}


def _link(path: str) -> str:
    base = (settings.APP_PUBLIC_URL or "http://localhost:5173").rstrip("/")
    return f"{base}{path}"


def _user(db: Session, user_id: Optional[str]) -> Optional[User]:
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def _location(db: Session, building_id: Optional[str], room_id: Optional[str]) -> str:
    building = (
        db.query(Building).filter(Building.id == building_id).first()
        if building_id
        else None
    )
    room = db.query(Room).filter(Room.id == room_id).first() if room_id else None
    return email_templates.format_location(
        building.name if building else None,
        room.name if room else None,
    )


def _notify(
    db: Session,
    user: Optional[User],
    *,
    title: str,
    message: str,
    notif_type: str = "info",
    path: str,
) -> None:
    if not user:
        return
    notification_service.create_in_app_notification(
        db=db,
        recipient_id=user.id,
        recipient_role=user.role,
        title=title,
        message=message,
        notif_type=notif_type,
        link_url=path,
    )


def _email(db: Session, user: Optional[User], subject: str, body: str) -> None:
    if not user or not user.email:
        return
    notification_service.queue_outbox_email(
        db=db,
        recipient_email=user.email,
        subject=subject,
        body=body,
    )


def _admin_users(db: Session) -> List[User]:
    """In-app audience: facilities coordinators plus system admins."""
    return (
        db.query(User)
        .filter(
            User.role == "admin",
            User.is_active.is_(True),
            User.sub_role.in_(["facilities_admin", "system_admin"]),
        )
        .all()
    )


def _admin_email_users(db: Session) -> List[User]:
    """Email only the operational owner, falling back to a system admin."""
    users = _admin_users(db)
    facilities = [u for u in users if u.sub_role == "facilities_admin"]
    if facilities:
        return facilities[:2]
    return users[:1]


def _reporters_for_incident(
    db: Session, incident_id: str
) -> List[Tuple[Report, User]]:
    reports = db.query(Report).filter(Report.incident_id == incident_id).all()
    seen = set()
    results: List[Tuple[Report, User]] = []
    for report in reports:
        if report.reporter_id in seen:
            continue
        reporter = _user(db, report.reporter_id)
        if reporter:
            seen.add(report.reporter_id)
            results.append((report, reporter))
    return results


def _reporter_path(report: Report) -> str:
    return _REPORTER_LINKS.get(report.reporter_role, "/student/requests")


def report_submitted(db: Session, report: Report) -> None:
    """Acknowledge the reporter and, when untriaged, alert the facilities desk."""
    reporter = _user(db, report.reporter_id)
    location = _location(db, report.building_id, report.room_id)
    incident = (
        db.query(Incident).filter(Incident.id == report.incident_id).first()
        if report.incident_id
        else None
    )

    if reporter:
        subject, body = email_templates.report_received(
            report_code=report.report_code,
            title=report.title,
            category=report.category,
            urgency=report.urgency,
            priority=_priority_for(report),
            location=location,
            submitted_at=report.created_at,
            reporter_name=reporter.name,
            link=_link(_reporter_path(report)),
            incident_code=incident.incident_code if incident else None,
        )
        _email(db, reporter, subject, body)
        _notify(
            db,
            reporter,
            title=(
                f"Report linked to {incident.incident_code}"
                if incident
                else f"Report {report.report_code} received"
            ),
            message=(
                f"Your report '{report.title}' was added to incident "
                f"{incident.incident_code}. You will be notified when it is resolved."
                if incident
                else (
                    f"Your report '{report.title}' is queued for facilities triage. "
                    "You will be notified when a work order is created."
                )
            ),
            path=_reporter_path(report),
        )

    if incident:
        return

    reporter_name = reporter.name if reporter else "A campus user"
    for admin in _admin_users(db):
        _notify(
            db,
            admin,
            title=f"New report needs triage: {report.report_code}",
            message=(
                f"{report.title} ({report.category}, {report.urgency}) reported at "
                f"{location}. Open triage to create the incident and dispatch a technician."
            ),
            notif_type="action_required",
            path="/admin/incidents",
        )

    for admin in _admin_email_users(db):
        subject, body = email_templates.admin_new_report(
            report_code=report.report_code,
            title=report.title,
            description=report.description,
            category=report.category,
            urgency=report.urgency,
            priority=_priority_for(report),
            location=location,
            reporter_name=reporter_name,
            submitted_at=report.created_at,
            link=_link("/admin/incidents"),
        )
        _email(db, admin, subject, body)


def report_triaged(
    db: Session,
    report: Report,
    incident: Incident,
    work_order: Optional[WorkOrder] = None,
    technician: Optional[User] = None,
) -> None:
    """Tell the reporter which incident and technician now own the issue."""
    reporter = _user(db, report.reporter_id)
    if not reporter:
        return

    location = _location(db, incident.building_id, incident.room_id)
    subject, body = email_templates.report_triaged(
        report_code=report.report_code,
        incident_code=incident.incident_code,
        incident_title=incident.title,
        priority=incident.priority,
        location=location,
        sla_due_at=incident.sla_due_at,
        work_order_code=work_order.work_order_code if work_order else None,
        technician_name=technician.name if technician else None,
        link=_link(_reporter_path(report)),
    )
    _email(db, reporter, subject, body)

    if work_order and technician:
        detail = (
            f"Work order {work_order.work_order_code} was assigned to "
            f"{technician.name}."
        )
    elif work_order:
        detail = f"Work order {work_order.work_order_code} is awaiting a technician."
    else:
        detail = "A work order will be created next."

    _notify(
        db,
        reporter,
        title=f"{incident.incident_code} created for your report",
        message=(
            f"Your report '{report.report_code}' is now tracked as "
            f"{incident.incident_code} ({incident.priority}). {detail}"
        ),
        path=_reporter_path(report),
    )


def work_order_assigned(
    db: Session,
    work_order: WorkOrder,
    incident: Optional[Incident],
    technician: Optional[User],
    is_reassignment: bool = False,
) -> None:
    """Notify the technician that a job is theirs; reporters only on reassignment."""
    if not technician:
        return

    location = _location(
        db,
        incident.building_id if incident else None,
        incident.room_id if incident else None,
    )

    try:
        required_skills = (
            json.loads(work_order.required_skills)
            if work_order.required_skills
            else []
        )
    except Exception:
        required_skills = []

    subject, body = email_templates.work_order_assigned(
        work_order_code=work_order.work_order_code,
        title=work_order.title,
        description=work_order.description,
        priority=work_order.priority,
        location=location,
        sla_deadline=work_order.sla_deadline,
        incident_code=incident.incident_code if incident else "Not linked",
        required_skills=required_skills,
        technician_name=technician.name,
        link=_link("/technician/tasks"),
        is_reassignment=is_reassignment,
    )
    _email(db, technician, subject, body)
    _notify(
        db,
        technician,
        title=(
            f"Work order {work_order.work_order_code} reassigned to you"
            if is_reassignment
            else f"Work order {work_order.work_order_code} assigned to you"
        ),
        message=(
            f"{work_order.title} - {work_order.priority}, due "
            f"{email_templates._fmt(work_order.sla_deadline)}."
        ),
        notif_type="action_required",
        path="/technician/tasks",
    )

    if is_reassignment and incident:
        for report, reporter in _reporters_for_incident(db, incident.id):
            _notify(
                db,
                reporter,
                title=f"Technician updated for {incident.incident_code}",
                message=(
                    f"{technician.name} is now handling work order "
                    f"{work_order.work_order_code} for your report {report.report_code}."
                ),
                path=_reporter_path(report),
            )


def work_order_created(
    db: Session,
    work_order: WorkOrder,
    incident: Incident,
    technician: Optional[User],
) -> None:
    """Inform reporters when an admin creates a work order outside triage."""
    for report, reporter in _reporters_for_incident(db, incident.id):
        location = _location(db, incident.building_id, incident.room_id)
        subject, body = email_templates.report_triaged(
            report_code=report.report_code,
            incident_code=incident.incident_code,
            incident_title=incident.title,
            priority=incident.priority,
            location=location,
            sla_due_at=incident.sla_due_at,
            work_order_code=work_order.work_order_code,
            technician_name=technician.name if technician else None,
            link=_link(_reporter_path(report)),
        )
        _email(db, reporter, subject, body)
        _notify(
            db,
            reporter,
            title=f"Work order {work_order.work_order_code} created",
            message=(
                f"{incident.incident_code}: work order {work_order.work_order_code} "
                f"was created"
                + (f" and assigned to {technician.name}." if technician else ".")
            ),
            path=_reporter_path(report),
        )


def work_order_unassigned(
    db: Session, work_order: WorkOrder, incident: Optional[Incident], reason: str = ""
) -> None:
    for admin in _admin_users(db):
        _notify(
            db,
            admin,
            title=f"Work order {work_order.work_order_code} needs a technician",
            message=(
                f"{work_order.title} could not be auto-dispatched. "
                f"{reason or 'No eligible technician was available.'} "
                "Assign a technician manually."
            ),
            notif_type="action_required",
            path="/admin/work-orders",
        )


def work_in_progress(
    db: Session, work_order: WorkOrder, incident: Optional[Incident]
) -> None:
    if not incident:
        return
    for report, reporter in _reporters_for_incident(db, incident.id):
        _notify(
            db,
            reporter,
            title=f"Work started on {incident.incident_code}",
            message=(
                f"A technician has started work order {work_order.work_order_code} "
                f"for your report {report.report_code}."
            ),
            path=_reporter_path(report),
        )


def work_order_completed(
    db: Session,
    work_order: WorkOrder,
    incident: Incident,
    technician: Optional[User],
) -> None:
    location = _location(db, incident.building_id, incident.room_id)
    technician_name = technician.name if technician else "Campus facilities"

    for report, reporter in _reporters_for_incident(db, incident.id):
        subject, body = email_templates.incident_resolved(
            report_code=report.report_code,
            incident_code=incident.incident_code,
            incident_title=incident.title,
            location=location,
            work_order_code=work_order.work_order_code,
            technician_name=technician_name,
            completed_at=work_order.completed_at,
            diagnosis=work_order.diagnosis,
            reporter_name=reporter.name,
            link=_link(_reporter_path(report)),
        )
        _email(db, reporter, subject, body)
        _notify(
            db,
            reporter,
            title=f"{incident.incident_code} resolved",
            message=(
                f"The issue you reported as {report.report_code} has been resolved "
                f"by {technician_name} ({work_order.work_order_code})."
            ),
            notif_type="info",
            path=_reporter_path(report),
        )


def _priority_for(report: Report) -> str:
    mapping = {
        "critical": "P1",
        "high": "P2",
        "medium": "P3",
        "low": "P4",
    }
    return mapping.get((report.urgency or "").lower(), "P3")
