import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.models.report import Report
from app.database.models.incident import Incident
from app.database.models.work_order import WorkOrder
from app.database.models.inventory import StockReservation
from app.database.models.approval import ApprovalRequest, ProcurementRequest
from app.database.models.notification import Notification, NotificationOutbox
from app.database.models.audit import AuditLog

def seed_incidents(db: Session, rooms, assets, users_dict, inventory_items):
    technicians = users_dict["technicians"]
    faculty = users_dict["faculty"]
    students = users_dict["students"]
    admins = users_dict["admins"]

    now = datetime.utcnow()
    incidents = []
    work_orders = []

    categories = ["network", "classroom", "electrical", "cleanliness", "safety", "equipment"]
    severities = ["low", "medium", "high", "critical"]
    priorities = ["P4", "P3", "P2", "P1"]

    incident_titles = {
        "network": ["Wi-Fi connectivity drop", "PoE switch offline", "DNS resolution failure", "High latency on access point", "Ethernet port disconnected"],
        "classroom": ["Projector lamp failed", "Smart podium display flickering", "Microphone audio distorted", "Motorized screen jammed", "AC remote missing"],
        "electrical": ["Circuit breaker tripped", "Power socket sparking", "UPS continuous beep alert", "Emergency exit light dead", "Flickering overhead LED panel"],
        "cleanliness": ["Chemical spill in storage aisle", "Hand sanitizer dispenser empty", "Whiteboard permanent marker residue", "Spilled drink on carpet", "Restroom water overflow"],
        "safety": ["Fire door latch blocked", "First aid kit tamper seal broken", "Eyewash station pressure low", "Fume hood airflow low warning", "Loose floor cable hazard"],
        "equipment": ["3D printer nozzle clogged", "Oscilloscope calibration expired", "Centrifuge rotor unbalanced", "Workstation won't boot into OS", "Soldering station overheat"]
    }

    # Generate 100 incidents
    for i in range(100):
        cat = categories[i % len(categories)]
        room = rooms[i % len(rooms)]
        asset = assets[i % len(assets)]
        reporter = students[i % len(students)] if i % 2 == 0 else faculty[i % len(faculty)]
        title_base = incident_titles[cat][i % len(incident_titles[cat])]
        title = f"{title_base} in {room.name}"
        sev = severities[i % len(severities)]
        prio = priorities[i % len(priorities)]

        # Time distribution across the past 30 days
        created_dt = now - timedelta(days=29 - (i % 30), hours=(i % 24), minutes=(i * 7) % 60)
        
        # State distribution
        if i < 20:
            status = "open"
            resolved_dt = None
        elif i < 45:
            status = "in_progress"
            resolved_dt = None
        elif i < 55:
            status = "pending_parts"
            resolved_dt = None
        elif i < 65:
            status = "pending_approval"
            resolved_dt = None
        else:
            status = "resolved" if i < 90 else "closed"
            resolved_dt = created_dt + timedelta(hours=4, minutes=30)

        # SLA calculation
        sla_hours = 4 if prio == "P1" else (12 if prio == "P2" else (48 if prio == "P3" else 96))
        sla_due = created_dt + timedelta(hours=sla_hours)
        is_breached = (now > sla_due and status not in ["resolved", "closed"]) or (resolved_dt and resolved_dt > sla_due)

        incident = Incident(
            incident_code=f"INC-2026-{i+1:04d}",
            title=title,
            description=f"Automated sensor report / user ticket: {title_base}. Room {room.room_number}. Impact: {sev} priority operational degradation.",
            category=cat,
            severity=sev,
            priority=prio,
            building_id=room.building_id,
            room_id=room.id,
            asset_id=asset.id,
            status=status,
            sla_due_at=sla_due,
            is_sla_breached=is_breached,
            correlated_count=1 + (i % 4),
            summary=f"Incident tracked for {room.name}. Category: {cat.capitalize()}.",
            resolved_at=resolved_dt,
            created_at=created_dt,
            updated_at=resolved_dt or created_dt
        )
        db.add(incident)
        db.flush()
        incidents.append(incident)

        # Create linked report
        report = Report(
            report_code=f"RPT-2026-{i+1:04d}",
            title=title,
            description=f"User report: {title_base}. Please dispatch technician immediately.",
            category=cat,
            urgency=sev,
            building_id=room.building_id,
            room_id=room.id,
            asset_id=asset.id,
            reporter_id=reporter.id,
            reporter_role=reporter.role,
            source="web_portal" if i % 4 != 0 else "simulated_email",
            status="correlated" if status != "resolved" else "resolved",
            incident_id=incident.id,
            ai_extracted_meta=json.dumps({
                "category": cat,
                "urgency": sev,
                "confidence": 0.94,
                "room_matched": room.room_number
            }),
            created_at=created_dt
        )
        db.add(report)

    # Generate 60 work orders linked to first 60 incidents
    wo_statuses = ["assigned", "in_progress", "blocked", "pending_parts", "completed"]
    for j in range(60):
        inc = incidents[j]
        tech = technicians[j % len(technicians)]
        wo_status = "completed" if inc.status in ["resolved", "closed"] else (
            "pending_parts" if inc.status == "pending_parts" else (
                "blocked" if j % 7 == 0 else (
                    "in_progress" if inc.status == "in_progress" else "assigned"
                )
            )
        )

        wo = WorkOrder(
            work_order_code=f"WO-2026-{j+1:04d}",
            incident_id=inc.id,
            title=f"Repair: {inc.title}",
            description=f"Action item for {inc.incident_code}: Onsite inspection, component isolation and repair validation.",
            assigned_technician_id=tech.id,
            priority=inc.priority,
            status=wo_status,
            required_skills=json.dumps([inc.category, "hardware"]),
            sla_deadline=inc.sla_due_at,
            blocked_reason="Missing replacement module" if wo_status in ["blocked", "pending_parts"] else None,
            diagnosis=f"Inspected {inc.category} asset. Diagnosed hardware signal fault." if wo_status != "assigned" else None,
            checklist=json.dumps([
                {"task": "Verify power and cabling", "done": wo_status in ["in_progress", "completed", "pending_parts"]},
                {"task": "Run diagnostic loopback", "done": wo_status in ["completed"]},
                {"task": "Post-maintenance verification signoff", "done": wo_status == "completed"}
            ]),
            evidence_notes="Photos and logs captured during inspection." if wo_status == "completed" else None,
            completed_at=inc.resolved_at if wo_status == "completed" else None,
            created_at=inc.created_at
        )
        db.add(wo)
        db.flush()
        work_orders.append(wo)

        # Seed some stock reservations
        if j % 4 == 0:
            inv = inventory_items[j % len(inventory_items)]
            res = StockReservation(
                work_order_id=wo.id,
                item_id=inv.id,
                quantity=1,
                status="consumed" if wo_status == "completed" else "reserved",
                created_at=inc.created_at
            )
            db.add(res)

    # Seed some approval requests and procurement requests
    procurement_mgr = next(u for u in admins if u.sub_role == "procurement_approver")
    dept_mgr = next(u for u in admins if u.sub_role == "department_manager")
    facilities_admin = next(u for u in admins if u.sub_role == "facilities_admin")

    app1 = ApprovalRequest(
        approval_type="purchase",
        target_entity_type="procurement",
        target_entity_id=inventory_items[0].id,
        requester_id=facilities_admin.id,
        approver_id=None,
        status="pending",
        cost_amount=900.0,
        justification="Urgent stock replenishment for 2x Enterprise Wi-Fi 6 AP Modules."
    )
    db.add(app1)

    app2 = ApprovalRequest(
        approval_type="costly_repair",
        target_entity_type="work_order",
        target_entity_id=work_orders[0].id,
        requester_id=facilities_admin.id,
        approver_id=dept_mgr.id,
        status="approved",
        cost_amount=1450.0,
        justification="Emergency transformer coil repair in Science Block.",
        decision_reason="Approved under critical operations budget.",
        decided_at=now - timedelta(days=2)
    )
    db.add(app2)

    app3 = ApprovalRequest(
        approval_type="room_override",
        target_entity_type="room",
        target_entity_id=rooms[0].id,
        requester_id=faculty[0].id,
        approver_id=None,
        status="pending",
        cost_amount=0.0,
        justification="Requesting temporary weekend exam hall override for CS hackathon."
    )
    db.add(app3)

    # Seed Notifications
    notif1 = Notification(
        recipient_id=technicians[0].id,
        recipient_role="technician",
        title="New Work Order Assigned",
        message=f"Work Order {work_orders[0].work_order_code} assigned to you: {work_orders[0].title}",
        type="action_required",
        read=False,
        link_url=f"/technician/tasks/{work_orders[0].id}"
    )
    db.add(notif1)

    notif2 = Notification(
        recipient_id=admins[0].id,
        recipient_role="admin",
        title="SLA Alert: High Priority Incident",
        message="INC-2026-0004 approaching SLA deadline (less than 1 hour remaining).",
        type="warning",
        read=False,
        link_url="/admin/incidents"
    )
    db.add(notif2)

    notif3 = Notification(
        recipient_id=faculty[0].id,
        recipient_role="faculty",
        title="Room Readiness Confirmed",
        message="Computer Lab A daily readiness check confirmed for today.",
        type="info",
        read=True,
        link_url="/faculty/timetable"
    )
    db.add(notif3)

    # Seed Notification Outbox
    outbox1 = NotificationOutbox(
        recipient_email=faculty[0].email,
        channel="email",
        subject="CampusOps: Schedule Confirmation",
        body="Your room booking BKG-EXAM-2026-001 has been confirmed.",
        status="sent",
        attempts=1,
        last_attempt_at=now - timedelta(hours=1)
    )
    db.add(outbox1)

    # Seed Audit Logs
    audit1 = AuditLog(
        action="INCIDENT_CREATED",
        actor_id=students[0].id,
        actor_role="student",
        entity_type="incident",
        entity_id=incidents[0].id,
        new_value=json.dumps({"incident_code": incidents[0].incident_code, "priority": incidents[0].priority}),
        reason="Report triaged and elevated to incident",
        created_at=now - timedelta(days=1)
    )
    db.add(audit1)

    audit2 = AuditLog(
        action="WORK_ORDER_ASSIGNED",
        actor_id=admins[0].id,
        actor_role="admin",
        entity_type="work_order",
        entity_id=work_orders[0].id,
        new_value=json.dumps({"technician_id": technicians[0].id, "status": "assigned"}),
        reason="Assigned matching skills and morning shift availability",
        created_at=now - timedelta(hours=18)
    )
    db.add(audit2)

    db.flush()
    return incidents, work_orders

