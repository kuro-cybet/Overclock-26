from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.notification_service import notification_service


class NotificationAdapter:
    """
    Thin facade over the outbox worker used by integration callers.

    It delegates to NotificationService so there is a single delivery path;
    previously it marked every queued email "sent" without actually sending.
    """

    def dispatch_outbox_queue(self, db: Session) -> Dict[str, Any]:
        result = notification_service.process_pending_outbox(db=db)
        return {
            "processed": result["processed"],
            "sent": result["sent"],
            "failed": result["failed"],
            "delivery_mode": result["delivery_mode"],
            "status": "processed",
        }


notification_adapter = NotificationAdapter()
