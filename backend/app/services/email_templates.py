"""Plain-text email content for the CampusOps lifecycle notifications.

Every email is generated from the actual report / incident / work order data,
so the recipient sees the ticket code, the location, the assigned technician and
the SLA deadline instead of a generic integration message.
"""

from datetime import datetime
from typing import Optional


def _fmt(value: Optional[datetime]) -> str:
    if not value:
        return "Not set"
    return value.strftime("%d %b %Y, %H:%M UTC")


def format_location(building_name: Optional[str], room_name: Optional[str]) -> str:
    parts = [part for part in (building_name, room_name) if part]
    return " / ".join(parts) if parts else "Campus-wide"


def _signature(reference: str) -> list:
    return [
        "",
        "Regards,",
        "CampusOps Notification System",
        f"Reference: {reference}",
    ]


def report_received(
    *,
    report_code: str,
    title: str,
    category: str,
    urgency: str,
    priority: str,
    location: str,
    submitted_at: Optional[datetime],
    reporter_name: str,
    link: str,
    incident_code: Optional[str] = None,
) -> tuple:
    if incident_code:
        subject = f"CampusOps: Report {report_code} linked to {incident_code}"
        opening = (
            "Thanks for the report. It matched an existing campus incident, so it "
            "has been linked to that incident and the assigned team can see it."
        )
        next_steps = [
            "Facilities already has an active work order for this incident.",
            "You will receive another email when the work is resolved.",
        ]
    else:
        subject = f"CampusOps: Report {report_code} received"
        opening = (
            "Thanks for reporting this issue. Your report is now in the facilities "
            "triage queue."
        )
        next_steps = [
            "A facilities coordinator reviews the report and groups it with any related incidents.",
            "A work order is created and assigned to a qualified technician.",
            "You will receive another email as soon as the work is resolved.",
        ]

    lines = [
        f"Hi {reporter_name},",
        "",
        opening,
        "",
        f"Report: {report_code} - {title}",
        f"Category: {category}",
        f"Urgency: {urgency} ({priority})",
        f"Location: {location}",
        f"Submitted: {_fmt(submitted_at)}",
    ]

    if incident_code:
        lines.append(f"Incident: {incident_code}")

    lines.extend(["", "What happens next:"])
    lines.extend(f"{index}. {step}" for index, step in enumerate(next_steps, start=1))
    lines.extend(["", f"Track your report: {link}"])
    lines.extend(_signature(report_code))
    return subject, "\n".join(lines)


def admin_new_report(
    *,
    report_code: str,
    title: str,
    description: str,
    category: str,
    urgency: str,
    priority: str,
    location: str,
    reporter_name: str,
    submitted_at: Optional[datetime],
    link: str,
    incident_code: Optional[str] = None,
) -> tuple:
    subject = (
        f"CampusOps: New report {report_code} linked to {incident_code}"
        if incident_code
        else f"CampusOps: Action needed - {report_code} is waiting for triage"
    )
    opening = (
        f"A new report was linked to existing incident {incident_code}."
        if incident_code
        else "A new report needs triage."
    )
    body = "\n".join(
        [
            opening,
            "",
            f"Report: {report_code}",
            *([f"Incident: {incident_code}"] if incident_code else []),
            f"Title: {title}",
            f"Category: {category}",
            f"Urgency: {urgency} ({priority})",
            f"Location: {location}",
            f"Reporter: {reporter_name}",
            f"Submitted: {_fmt(submitted_at)}",
            "",
            "Description:",
            description,
            "",
            f"Open the triage queue: {link}",
        ]
        + _signature(report_code)
    )
    return subject, body


def report_triaged(
    *,
    report_code: str,
    incident_code: str,
    incident_title: str,
    priority: str,
    location: str,
    sla_due_at: Optional[datetime],
    work_order_code: Optional[str],
    technician_name: Optional[str],
    link: str,
) -> tuple:
    subject = f"CampusOps: {incident_code} created for your report {report_code}"

    if work_order_code and technician_name:
        dispatch = (
            f"A work order ({work_order_code}) has been created and assigned to "
            f"{technician_name}."
        )
    elif work_order_code:
        dispatch = (
            f"A work order ({work_order_code}) has been created and is waiting for "
            "a technician to be assigned."
        )
    else:
        dispatch = "A work order will be created for this incident."

    body = "\n".join(
        [
            "Your report has been reviewed and linked to a tracked incident.",
            "",
            f"Report: {report_code}",
            f"Incident: {incident_code} - {incident_title}",
            f"Priority: {priority}",
            f"Location: {location}",
            f"Target resolution: {_fmt(sla_due_at)}",
            "",
            dispatch,
            "You will receive another email when the work is resolved.",
            "",
            f"Track your report: {link}",
        ]
        + _signature(report_code)
    )
    return subject, body


def work_order_assigned(
    *,
    work_order_code: str,
    title: str,
    description: str,
    priority: str,
    location: str,
    sla_deadline: Optional[datetime],
    incident_code: str,
    required_skills: list,
    technician_name: str,
    link: str,
    is_reassignment: bool = False,
) -> tuple:
    action = "reassigned" if is_reassignment else "assigned"
    subject = f"CampusOps: Work order {work_order_code} {action} to you"

    body = "\n".join(
        [
            f"Hi {technician_name},",
            "",
            f"Work order {work_order_code} has been {action} to you.",
            "",
            f"Job: {title}",
            f"Incident: {incident_code}",
            f"Priority: {priority}",
            f"Location: {location}",
            f"SLA deadline: {_fmt(sla_deadline)}",
            f"Required skills: {', '.join(required_skills) if required_skills else 'General maintenance'}",
            "",
            "Description:",
            description,
            "",
            "Open the job to review the checklist and record your diagnosis:",
            link,
        ]
        + _signature(work_order_code)
    )
    return subject, body


def incident_resolved(
    *,
    report_code: str,
    incident_code: str,
    incident_title: str,
    location: str,
    work_order_code: Optional[str],
    technician_name: str,
    completed_at: Optional[datetime],
    diagnosis: Optional[str],
    reporter_name: str,
    link: str,
) -> tuple:
    subject = f"CampusOps: {incident_code} resolved"

    resolution = [
        f"Incident: {incident_code} - {incident_title}",
        f"Location: {location}",
        f"Work order: {work_order_code or 'Not linked'}",
        f"Technician: {technician_name}",
        f"Completed: {_fmt(completed_at)}",
    ]
    if diagnosis:
        resolution.extend(["", "Resolution notes:", diagnosis])

    body = "\n".join(
        [
            f"Hi {reporter_name},",
            "",
            f"The issue you reported as {report_code} has been resolved.",
            "",
            *resolution,
            "",
            f"View your report history: {link}",
        ]
        + _signature(incident_code)
    )
    return subject, body
