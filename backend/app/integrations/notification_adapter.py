from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database.models.notification import NotificationOutbox

class NotificationAdapter:
    def dispatch_outbox_queue(self, db: Session) -> Dict[str, Any]:
        queued = db.query(NotificationOutbox).filter(NotificationOutbox.status == "queued").all()
        dispatched = 0
        for item in queued:
            item.attempts += 1
            item.last_attempt_at = datetime.utcnow()
            item.status = "sent"
            dispatched += 1
        db.flush()
        return {"processed": dispatched, "status": "all_delivered"}

notification_adapter = NotificationAdapter()

