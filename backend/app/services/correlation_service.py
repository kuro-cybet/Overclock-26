import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.database.models.report import Report
from app.database.models.incident import Incident
from app.database.models.audit import AuditLog
from app.database.models.user import User
from app.database.models.work_order import WorkOrder
from app.services import work_order_service, workflow_notifications
from app.services.notification_service import notification_service

class CorrelationService:
    def correlate_reports_to_incident(
        self,
        db: Session,
        report_ids: List[str],
        target_incident_id: Optional[str] = None,
        canonical_title: Optional[str] = None,
        actor_id: str = "system",
        actor_role: str = "admin"
    ) -> Incident:
        reports = db.query(Report).filter(Report.id.in_(report_ids)).all()
        if not reports:
            raise ValueError("No matching reports found for correlation.")

        lead_report = reports[0]

        if target_incident_id:
            incident = db.query(Incident).filter(Incident.id == target_incident_id).first()
            if not incident:
                raise ValueError("Target incident does not exist.")
            incident.correlated_count += len(reports)
        else:
            # Create a new canonical incident
            inc_count = db.query(Incident).count()
            sla_hours = 4 if lead_report.urgency == "critical" else (12 if lead_report.urgency == "high" else 48)
            now = datetime.utcnow()

            title = canonical_title or f"Canonical Outage: {lead_report.title}"
            incident = Incident(
                incident_code=f"INC-{now.strftime('%Y%m')}-{inc_count + 1:04d}",
                title=title,
                description=f"Correlated operational incident grouping {len(reports)} independent reports. Initial symptom: {lead_report.description}",
                category=lead_report.category,
                severity=lead_report.urgency,
                priority="P1" if lead_report.urgency == "critical" else "P2",
                building_id=lead_report.building_id,
                room_id=lead_report.room_id,
                asset_id=lead_report.asset_id,
                status="open",
                sla_due_at=now + timedelta(hours=sla_hours),
                is_sla_breached=False,
                correlated_count=len(reports),
                summary=f"Incident aggregated from {len(reports)} user reports. Location proximity: Room {lead_report.room_id or 'Building wide'}."
            )
            db.add(incident)
            db.flush()

        # Update all reports to point to this incident
        for r in reports:
            r.incident_id = incident.id
            r.status = "correlated"

        db.flush()

        # Create the work order as part of triage and auto-dispatch the best
        # technician.  Dispatch failure is non-fatal: the order stays unassigned
        # and the facilities desk is alerted.
        work_order, technician = work_order_service.ensure_work_order_for_incident(
            db,
            incident,
            actor_id=actor_id,
        )

        # Tell every reporter which incident (and technician) now owns their issue via in-app, WhatsApp, and Email.
        for r in reports:
            workflow_notifications.report_triaged(
                db,
                r,
                incident,
                work_order=work_order,
                technician=technician,
            )
            reporter = db.query(User).filter(User.id == r.reporter_id).first()
            phone = getattr(r, 'contact_phone', None) or (reporter.phone_number if reporter else None)

            # WhatsApp notification
            if phone:
                wa_body = (
                    f"🔔 *Notice for Report {r.report_code}:*\n\n"
                    f"Your issue has been correlated into incident *{incident.incident_code}* (*{incident.title}*).\n\n"
                    f"• *Status:* {incident.status.title()}\n"
                    f"• *Technician:* {technician.name if technician else 'Facilities Team'}\n\n"
                    f"You will receive automatic updates via WhatsApp and email as work progresses."
                )
                notification_service.queue_whatsapp_notification(
                    db=db,
                    recipient_phone=phone,
                    body=wa_body,
                    idempotency_key=f"wa_correlate_{incident.incident_code}_{r.id}",
                    recipient_email=reporter.email if reporter else None,
                    subject=f"Notice: Report {r.report_code} linked to {incident.incident_code}"
                )

            # Email notification
            if reporter and reporter.email:
                email_body = (
                    f"Hi {reporter.name},\n\n"
                    f"Your report {r.report_code} ({r.title}) has been correlated into incident "
                    f"{incident.incident_code} ({incident.title}).\n\n"
                    f"Status: {incident.status.title()}\n"
                    f"Assigned Technician: {technician.name if technician else 'Facilities Team'}\n\n"
                    f"You can monitor live progress on your student portal: /student/requests\n\n"
                    f"— CampusOps Facilities Support"
                )
                notification_service.queue_outbox_email(
                    db=db,
                    recipient_email=reporter.email,
                    subject=f"CampusOps: Report {r.report_code} correlated to {incident.incident_code}",
                    body=email_body,
                    event_type="report_correlated",
                    idempotency_key=f"email_correlate_{incident.incident_code}_{r.id}"
                )

        # Audit event
        audit = AuditLog(
            action="REPORTS_CORRELATED",
            actor_id=actor_id,
            actor_role=actor_role,
            entity_type="incident",
            entity_id=incident.id,
            new_value=json.dumps({"correlated_reports": [r.report_code for r in reports]}),
            reason=f"Correlated {len(reports)} similar complaint reports into canonical incident."
        )
        db.add(audit)
        db.flush()

        return incident

    def merge_incidents(
        self,
        db: Session,
        primary_incident_id: str,
        duplicate_incident_ids: List[str],
        notes: Optional[str] = None,
        actor_id: str = "system",
        actor_role: str = "admin"
    ) -> Incident:
        """
        Consolidates one or more duplicate incidents into a primary canonical incident.
        1. Moves all Report records from duplicate incidents to the primary incident.
        2. Updates primary incident's correlated_count.
        3. Marks duplicate incidents as 'merged' and cancels duplicate work orders.
        4. Notifies all students from all merged reports via WhatsApp and Gmail.
        """
        primary = db.query(Incident).filter(Incident.id == primary_incident_id).first()
        if not primary:
            raise ValueError(f"Primary incident {primary_incident_id} not found.")

        dup_ids = [d for d in duplicate_incident_ids if d != primary.id]
        duplicates = db.query(Incident).filter(Incident.id.in_(dup_ids)).all()
        if not duplicates:
            raise ValueError("No valid duplicate incidents found to merge.")

        work_order, technician = work_order_service.ensure_work_order_for_incident(
            db, primary, actor_id=actor_id
        )

        all_migrated_reports = []
        for dup in duplicates:
            dup_reports = db.query(Report).filter(Report.incident_id == dup.id).all()
            for r in dup_reports:
                r.incident_id = primary.id
                r.status = "correlated"
                all_migrated_reports.append(r)
                primary.correlated_count += 1

            db.query(WorkOrder).filter(WorkOrder.incident_id == dup.id).update(
                {"status": "cancelled", "evidence_notes": f"Duplicate cancelled: Merged into master incident {primary.incident_code}"},
                synchronize_session=False
            )

            dup.status = "merged"
            dup.summary = f"Duplicate incident consolidated into canonical {primary.incident_code}."

        primary.summary = (
            f"Consolidated incident aggregating {primary.correlated_count} user reports. "
            f"{notes or ''}".strip()
        )
        db.flush()

        # Notify ALL reporters across all linked reports of the primary incident
        all_incident_reports = db.query(Report).filter(Report.incident_id == primary.id).all()
        for r in all_incident_reports:
            reporter = db.query(User).filter(User.id == r.reporter_id).first()
            phone = getattr(r, 'contact_phone', None) or (reporter.phone_number if reporter else None)

            workflow_notifications.report_triaged(
                db, r, primary, work_order=work_order, technician=technician
            )

            if phone:
                wa_body = (
                    f"🔔 *Notice for Report {r.report_code}:*\n\n"
                    f"Your issue has been merged into master incident *{primary.incident_code}* (*{primary.title}*).\n\n"
                    f"• *Status:* {primary.status.title()}\n"
                    f"• *Total Reports Combined:* {primary.correlated_count}\n"
                    f"• *Technician:* {technician.name if technician else 'Facilities Team'}\n\n"
                    f"You will receive automatic updates via WhatsApp and email as work progresses."
                )
                notification_service.queue_whatsapp_notification(
                    db=db,
                    recipient_phone=phone,
                    body=wa_body,
                    idempotency_key=f"wa_merge_{primary.incident_code}_{r.id}",
                    recipient_email=reporter.email if reporter else None,
                    subject=f"Notice: Report {r.report_code} consolidated into {primary.incident_code}"
                )

            if reporter and reporter.email:
                email_body = (
                    f"Hi {reporter.name},\n\n"
                    f"Your report {r.report_code} ({r.title}) has been merged into master incident "
                    f"{primary.incident_code} ({primary.title}).\n\n"
                    f"Our facilities team has consolidated these duplicate reports to prioritize technician dispatch.\n\n"
                    f"Status: {primary.status.title()}\n"
                    f"Combined Reports: {primary.correlated_count}\n"
                    f"Assigned Technician: {technician.name if technician else 'Facilities Team'}\n\n"
                    f"You can monitor live progress on your student portal: /student/requests\n\n"
                    f"— CampusOps Facilities Support"
                )
                notification_service.queue_outbox_email(
                    db=db,
                    recipient_email=reporter.email,
                    subject=f"CampusOps: Report {r.report_code} merged into {primary.incident_code}",
                    body=email_body,
                    event_type="report_correlated",
                    idempotency_key=f"email_merge_{primary.incident_code}_{r.id}"
                )

        audit = AuditLog(
            action="INCIDENTS_MERGED",
            actor_id=actor_id,
            actor_role=actor_role,
            entity_type="incident",
            entity_id=primary.id,
            new_value=json.dumps({
                "primary_incident": primary.incident_code,
                "merged_duplicate_ids": dup_ids,
                "migrated_reports": [r.report_code for r in all_migrated_reports]
            }),
            reason=f"Merged {len(dup_ids)} duplicate incidents into master incident {primary.incident_code}."
        )
        db.add(audit)
        db.flush()
        return primary

correlation_service = CorrelationService()

