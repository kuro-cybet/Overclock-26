from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.intake_service import intake_service
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
            source="simulated_email",
            reporter_email=sender_email,
        )

        report = result["report"]

        return {
            "status": "processed",
            "report_code": report.report_code,
            "category": report.category,
            "urgency": report.urgency,
            "outbox_id": result["outbox_id"],
            "delivery_status": "queued" if result["outbox_id"] else None,
            "ai_extracted": result["ai_extraction"]
        }

simulated_email_service = SimulatedEmailService()
