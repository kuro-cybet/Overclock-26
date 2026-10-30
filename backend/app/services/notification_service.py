from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from app.database.models.notification import Notification, NotificationOutbox
from app.database.models.user import User

class NotificationService:
    def create_in_app_notification(
        self,
        db: Session,
        recipient_id: str,
        recipient_role: str,
        title: str,
        message: str,
        notif_type: str = "info",
        link_url: Optional[str] = None
    ) -> Notification:
        notif = Notification(
            recipient_id=recipient_id,
            recipient_role=recipient_role,
            title=title,
            message=message,
            type=notif_type,
            read=False,
            link_url=link_url
        )
        db.add(notif)
        db.flush()
        return notif

    def broadcast_role_notification(
        self,
        db: Session,
        role: str,
        title: str,
        message: str,
        notif_type: str = "info",
        link_url: Optional[str] = None
    ) -> List[Notification]:
        users = db.query(User).filter(User.role == role).all()
        created = []
        for u in users:
            n = Notification(
                recipient_id=u.id,
                recipient_role=role,
                title=title,
                message=message,
                type=notif_type,
                read=False,
                link_url=link_url
            )
            db.add(n)
            created.append(n)
        db.flush()
        return created

    def queue_outbox_email(
        self,
        db: Session,
        recipient_email: str,
        subject: str,
        body: str,
        channel: str = "email"
    ) -> NotificationOutbox:
        outbox = NotificationOutbox(
            recipient_email=recipient_email,
            channel=channel,
            subject=subject,
            body=body,
            status="sent",  # simulated instant delivery
            attempts=1,
            last_attempt_at=datetime.utcnow()
        )
        db.add(outbox)
        db.flush()
        return outbox

notification_service = NotificationService()

