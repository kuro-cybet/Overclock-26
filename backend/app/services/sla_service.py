from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.database.models.incident import Incident
from app.database.models.work_order import WorkOrder
from app.services.notification_service import notification_service

class SLAService:
    # Priority based SLA targets in hours
    SLA_HOURS = {
        "P1": 4,    # Critical - 4 hours
        "P2": 12,   # High - 12 hours
        "P3": 48,   # Medium - 48 hours
        "P4": 96    # Low - 96 hours
    }

    def calculate_deadline(self, priority: str, start_time: datetime = None) -> datetime:
        base = start_time or datetime.utcnow()
        hours = self.SLA_HOURS.get(priority, 48)
        return base + timedelta(hours=hours)

    def evaluate_all_incidents_sla(self, db: Session) -> Dict[str, Any]:
        now = datetime.utcnow()
        active_incidents = db.query(Incident).filter(
            Incident.status.in_(["open", "in_progress", "pending_parts", "pending_approval"])
        ).all()

        breached_count = 0
        approaching_count = 0
        escalations = []

        for inc in active_incidents:
            if not inc.sla_due_at:
                inc.sla_due_at = self.calculate_deadline(inc.priority, inc.created_at)

            # Check if breached
            if now > inc.sla_due_at:
                if not inc.is_sla_breached:
                    inc.is_sla_breached = True
                    # Escalate: create notification
                    notification_service.broadcast_role_notification(
                        db=db,
                        role="admin",
                        title=f"SLA Breach Escalation: {inc.incident_code}",
                        message=f"Incident '{inc.title}' has breached its resolution SLA deadline! Priority: {inc.priority}.",
                        notif_type="critical",
                        link_url=f"/admin/incidents"
                    )
                breached_count += 1
                escalations.append({
                    "incident_id": inc.id,
                    "code": inc.incident_code,
                    "status": "breached",
                    "due_at": inc.sla_due_at.isoformat()
                })
            elif (inc.sla_due_at - now).total_seconds() < 3600:  # less than 1 hour remaining
                approaching_count += 1
                escalations.append({
                    "incident_id": inc.id,
                    "code": inc.incident_code,
                    "status": "warning_under_1hr",
                    "due_at": inc.sla_due_at.isoformat()
                })

        db.flush()
        return {
            "total_active": len(active_incidents),
            "breached": breached_count,
            "warning": approaching_count,
            "escalations": escalations
        }

sla_service = SLAService()

