import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.database.models.notification import Notification, NotificationOutbox
from app.database.models.user import User
from app.integrations.gmail_sender import EmailDeliveryError, gmail_sender

logger = logging.getLogger(__name__)

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

    def create_notification(
        self,
        db: Session,
        recipient_id: str,
        title: str,
        message: str,
        severity: str = "info",
        link_url: Optional[str] = None
    ) -> Notification:
        """Convenience helper that resolves recipient role if not supplied."""
        role = "user"
        if recipient_id == "admin":
            role = "admin"
        else:
            user = db.query(User).filter(User.id == recipient_id).first()
            if user:
                role = user.role

        return self.create_in_app_notification(
            db=db,
            recipient_id=recipient_id,
            recipient_role=role,
            title=title,
            message=message,
            notif_type=severity,
            link_url=link_url
        )

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
            status="queued",
            attempts=0,
            last_attempt_at=None
        )
        db.add(outbox)
        db.flush()
        return outbox

    def process_pending_outbox(self, db: Session, max_items: int = 25) -> Dict[str, Any]:
        """
        Processes pending notifications in the outbox with retry logic and exponential backoff.
        Controlled backoff delays:
        - attempt 0: process immediately
        - attempt 1: wait >= 10s from last_attempt_at
        - attempt 2: wait >= 30s from last_attempt_at
        - attempt >= 3: mark failed (max retries exceeded)

        Delivery goes through the Gmail edge function when it is configured;
        otherwise it is simulated so local development and tests keep working.

        Each row is claimed atomically (status "processing") before the network
        call, so the background worker and a manual trigger cannot both deliver
        the same email. Rows abandoned by a crash are requeued after 5 minutes.
        """
        now = datetime.utcnow()

        # Recover rows left in "processing" by a crashed worker.
        db.query(NotificationOutbox).filter(
            NotificationOutbox.status == "processing",
            NotificationOutbox.last_attempt_at.isnot(None),
            NotificationOutbox.last_attempt_at < now - timedelta(minutes=5),
        ).update({"status": "queued"}, synchronize_session=False)

        candidates = (
            db.query(NotificationOutbox)
            .filter(NotificationOutbox.status == "queued")
            .limit(max_items * 2)
            .all()
        )

        sent_count = 0
        failed_count = 0
        skipped_count = 0

        for item in candidates:
            # Check maximum attempts
            if item.attempts >= 3:
                item.status = "failed"
                db.commit()
                failed_count += 1
                continue

            # Controlled exponential backoff check
            if item.last_attempt_at:
                delta = (now - item.last_attempt_at).total_seconds()
                required_delay = 10 if item.attempts == 1 else (30 if item.attempts == 2 else 0)
                if delta < required_delay:
                    skipped_count += 1
                    continue

            # Claim the row atomically; only one worker can win this update.
            claimed = (
                db.query(NotificationOutbox)
                .filter(
                    NotificationOutbox.id == item.id,
                    NotificationOutbox.status == "queued",
                )
                .update(
                    {
                        "status": "processing",
                        "attempts": NotificationOutbox.attempts + 1,
                        "last_attempt_at": now,
                    },
                    synchronize_session=False,
                )
            )

            # Commit the claim before the network call so the SQLite write lock
            # is not held during the Gmail round-trip.
            db.commit()

            if claimed != 1:
                skipped_count += 1
                continue

            db.refresh(item)

            try:
                gmail_sender.send(
                    recipient=item.recipient_email,
                    subject=item.subject,
                    body=item.body,
                    entity_code=item.id,
                )
                item.status = "sent"
                sent_count += 1
            except EmailDeliveryError as e:
                logger.error(f"[Outbox] Delivery failed for {item.recipient_email}: {e}")
                item.status = "failed" if item.attempts >= 3 else "queued"
                failed_count += 1
            except Exception as e:
                logger.error(f"[Outbox] Unexpected delivery error for {item.recipient_email}: {e}")
                item.status = "failed" if item.attempts >= 3 else "queued"
                failed_count += 1

            db.commit()
        return {
            "processed": sent_count + failed_count,
            "sent": sent_count,
            "failed": failed_count,
            "skipped_backoff": skipped_count,
            "delivery_mode": gmail_sender.mode,
            "timestamp": now.isoformat()
        }

notification_service = NotificationService()
