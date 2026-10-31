import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.database.models.notification import Notification, NotificationOutbox
from app.database.models.user import User
from app.integrations.gmail_sender import EmailDeliveryError, gmail_sender

logger = logging.getLogger(__name__)

EMAIL_EVENT_TYPES = frozenset({"report_submitted", "incident_resolved", "incident_update", "report_correlated"})


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
        event_type: str,
        channel: str = "email",
        idempotency_key: Optional[str] = None,
    ) -> NotificationOutbox:
        if channel == "email" and event_type not in EMAIL_EVENT_TYPES:
            raise ValueError(f"Unsupported email lifecycle event: {event_type}")

        if idempotency_key:
            existing = (
                db.query(NotificationOutbox)
                .filter(NotificationOutbox.idempotency_key == idempotency_key)
                .first()
            )
            if existing:
                logger.info(f"[Outbox] Duplicate email event ignored: {idempotency_key}")
                return existing

        outbox = NotificationOutbox(
            recipient_email=recipient_email,
            channel=channel,
            event_type=event_type,
            subject=subject,
            body=body,
            status="queued",
            attempts=0,
            last_attempt_at=None,
            idempotency_key=idempotency_key,
        )
        db.add(outbox)
        db.flush()
        return outbox

    def queue_whatsapp_notification(
        self,
        db: Session,
        recipient_phone: str,
        body: str,
        idempotency_key: Optional[str] = None,
        recipient_email: Optional[str] = None,
        subject: str = "Ticket Status Update"
    ) -> Optional[NotificationOutbox]:
        """
        Enqueues an outbound WhatsApp notification into the transactional outbox.
        Guarantees idempotency via idempotency_key to prevent duplicate WhatsApp messages.
        """
        clean_phone = recipient_phone.replace("+", "").strip()

        if idempotency_key:
            existing = (
                db.query(NotificationOutbox)
                .filter(NotificationOutbox.idempotency_key == idempotency_key)
                .first()
            )
            if existing:
                logger.info(f"[Outbox] Duplicate WhatsApp event ignored: {idempotency_key}")
                return existing

        outbox = NotificationOutbox(
            recipient_email=recipient_email or f"{clean_phone}@whatsapp",
            recipient_phone=clean_phone,
            channel="whatsapp",
            subject=subject,
            body=body,
            status="queued",
            attempts=0,
            last_attempt_at=None,
            idempotency_key=idempotency_key
        )
        db.add(outbox)
        db.flush()
        logger.info(f"[Outbox] Queued WhatsApp notification for {clean_phone}: {idempotency_key}")
        return outbox

    def notify_ticket_state_change(
        self,
        db: Session,
        incident_id: str,
        new_status: str,
        extra_details: Optional[str] = None
    ):
        """
        Finds the student/faculty member who submitted the ticket and dispatches
        a real-time WhatsApp status notification via the transactional outbox.
        """
        from app.database.models.incident import Incident
        from app.database.models.report import Report
        from app.database.models.whatsapp import WhatsAppUserLink

        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return

        # Find all linked reports to identify original reporters
        reports = db.query(Report).filter(Report.incident_id == incident.id).all()
        for report in reports:
            # Check if reporter has verified WhatsApp
            link = (
                db.query(WhatsAppUserLink)
                .filter(WhatsAppUserLink.user_id == report.reporter_id, WhatsAppUserLink.is_verified == True)
                .first()
            )
            user = db.query(User).filter(User.id == report.reporter_id).first()
            phone = link.phone_number if link else (user.phone_number if (user and user.whatsapp_verified) else getattr(report, 'contact_phone', None))

            if not phone:
                continue

            # Format status message per specifications
            status_title = new_status.replace("_", " ").title()
            if new_status in ["resolved", "closed", "completed"]:
                body = (
                    f"🎉 *Your ticket {incident.incident_code} has been marked as resolved.*\n\n"
                    f"The reported {incident.category} issue has been marked as completed.\n\n"
                    f"Thank you for using CampusOps."
                )
                subject = f"Ticket {incident.incident_code} resolved"
            elif new_status == "in_progress":
                body = (
                    f"🔔 *Update for Ticket {incident.incident_code}:*\n\n"
                    f"*Status:* Work in Progress\n\n"
                    f"Your complaint is now being addressed. {extra_details or 'A technician has started inspecting and servicing the issue.'}"
                )
                subject = f"Ticket {incident.incident_code} in_progress"
            elif new_status == "assigned":
                body = (
                    f"🔔 *Update for Ticket {incident.incident_code}:*\n\n"
                    f"*Status:* Assigned\n\n"
                    f"Your complaint has been assigned to a technician. {extra_details or ''}"
                )
                subject = f"Ticket {incident.incident_code} assigned"
            elif new_status in ["pending_parts", "blocked"]:
                body = (
                    f"🔔 *Update for Ticket {incident.incident_code}:*\n\n"
                    f"*Status:* Waiting for Resources\n\n"
                    f"{extra_details or 'Required replacement parts have been requisitioned for this work order.'}"
                )
                subject = f"Ticket {incident.incident_code} {new_status}"
            else:
                body = (
                    f"🔔 *Update for Ticket {incident.incident_code}:*\n\n"
                    f"*Status:* {status_title}\n\n"
                    f"{extra_details or f'Your ticket status has been updated to {status_title}.'}"
                )
                subject = f"Ticket {incident.incident_code} {new_status}"

            if phone:
                idempotency_key = f"wa_ticket_{incident.incident_code}_{new_status}_{report.reporter_id}"
                self.queue_whatsapp_notification(
                    db=db,
                    recipient_phone=phone,
                    body=body,
                    idempotency_key=idempotency_key,
                    recipient_email=user.email if user else None,
                    subject=subject
                )

            # Dispatch email notification to student's registered email
            if user and user.email:
                email_body = (
                    f"Hi {user.name},\n\n"
                    f"{body.replace('*', '')}\n\n"
                    f"Incident Code: {incident.incident_code}\n"
                    f"Report Code: {report.report_code}\n"
                    f"Status: {status_title}\n\n"
                    f"You can view live updates on your student portal at /student/requests.\n\n"
                    f"— CampusOps Facilities Support"
                )
                email_event = "incident_resolved" if new_status in ["resolved", "closed", "completed"] else "incident_update"
                email_idempotency_key = f"email_ticket_{incident.incident_code}_{new_status}_{report.reporter_id}"
                self.queue_outbox_email(
                    db=db,
                    recipient_email=user.email,
                    subject=f"CampusOps: {subject}",
                    body=email_body,
                    event_type=email_event,
                    idempotency_key=email_idempotency_key
                )

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
        from app.services.whatsapp_service import whatsapp_service

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
        simulated_count = 0

        for item in candidates:
            if item.channel == "email" and item.event_type not in EMAIL_EVENT_TYPES:
                logger.warning(
                    "[Outbox] Cancelled unclassified legacy email %s to %s.",
                    item.id,
                    item.recipient_email,
                )
                item.status = "cancelled"
                db.commit()
                skipped_count += 1
                continue

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
                if item.channel == "whatsapp" and item.recipient_phone:
                    # Execute WhatsApp Cloud API send synchronously in worker
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            send_future = asyncio.run_coroutine_threadsafe(
                                whatsapp_service.send_text_message(item.recipient_phone, item.body),
                                loop
                            )
                            send_res = send_future.result(timeout=10)
                        else:
                            send_res = loop.run_until_complete(
                                whatsapp_service.send_text_message(item.recipient_phone, item.body)
                            )
                    except Exception:
                        send_res = asyncio.run(
                            whatsapp_service.send_text_message(item.recipient_phone, item.body)
                        )

                    if send_res.get("status") in ["sent", "simulated"]:
                        item.status = "sent"
                        sent_count += 1
                    else:
                        item.status = "failed" if item.attempts >= 3 else "queued"
                        failed_count += 1
                else:
                    delivery = gmail_sender.send(
                        recipient=item.recipient_email,
                        subject=item.subject,
                        body=item.body,
                        entity_code=item.id,
                    )
                    if delivery.simulated:
                        item.status = "simulated"
                        simulated_count += 1
                    else:
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
            "simulated": simulated_count,
            "delivery_mode": gmail_sender.mode,
            "timestamp": now.isoformat()
        }

notification_service = NotificationService()
