import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.database.models.report import Report
from app.database.models.incident import Incident
from app.database.models.audit import AuditLog
from app.services import work_order_service, workflow_notifications

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

        # Tell every reporter which incident (and technician) now owns their issue.
        for r in reports:
            workflow_notifications.report_triaged(
                db,
                r,
                incident,
                work_order=work_order,
                technician=technician,
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

correlation_service = CorrelationService()

