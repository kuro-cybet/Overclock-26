from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.intake_service import intake_service
from app.services.notification_service import notification_service
from app.database.models.user import User

class SimulatedEmailService:
    def process_incoming_email(
        self,
        db: Session,
        sender_email: str,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        # Identify user or map to external reporter
        user = db.query(User).filter(User.email == sender_email).first()
        reporter_id = user.id if user else "external_email_user"
        reporter_role = user.role if user else "student"

        # Pass through intake and AI extraction
        result = intake_service.process_incoming_report(
            db=db,
            reporter_id=reporter_id,
            reporter_role=reporter_role,
            title=subject,
            description=body,
            source="simulated_email"
        )

        report = result["report"]

        # Produce notification outbox event with delivery-attempt record
        outbox_entry = notification_service.queue_outbox_email(
            db=db,
            recipient_email=sender_email,
            subject=f"CampusOps Ticket Acknowledgment: {report.report_code}",
            body=f"Hello,\n\nYour issue report '{report.title}' has been logged in CampusOps with reference ID {report.report_code}.\n"
                 f"Estimated classification: {report.category.capitalize()} (Urgency: {report.urgency.capitalize()}).\n\n"
                 f"Our campus operations dispatch team has received your ticket.",
            channel="email"
        )

        return {
            "status": "processed",
            "report_code": report.report_code,
            "category": report.category,
            "urgency": report.urgency,
            "outbox_id": outbox_entry.id,
            "delivery_status": outbox_entry.status,
            "ai_extracted": result["ai_extraction"]
        }

simulated_email_service = SimulatedEmailService()

