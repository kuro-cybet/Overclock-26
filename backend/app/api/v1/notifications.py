from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.notification import Notification, NotificationOutbox
from app.database.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    ReadAllResponse,
    OutboxProcessResponse,
    OutboxStatusResponse
)
from app.core.exceptions import EntityNotFoundError
from app.api.deps import get_current_user, require_admin_sub_role
from app.services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get(
    "",
    response_model=List[NotificationResponse],
    summary="List User Notifications",
    description="Retrieves in-app notification alerts targeted to the authenticated user ID or their broader campus role.",
    responses={
        401: {"description": "Authentication required"}
    }
)
def get_user_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List recent alerts for current user or user role.
    """
    notifs = db.query(Notification).filter(
        (Notification.recipient_id == current_user.id) |
        (Notification.recipient_role == current_user.role)
    ).order_by(Notification.created_at.desc()).limit(30).all()
    return notifs

@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark Notification as Read",
    description="Marks a specific notification alert as read.",
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Notification not found"}
    }
)
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark notification as read.
    """
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise EntityNotFoundError("Notification", notification_id)
    notif.read = True
    db.commit()
    db.refresh(notif)
    return notif

@router.post(
    "/read-all",
    response_model=ReadAllResponse,
    summary="Mark All Notifications Read",
    description="Marks all unread notifications addressed to the caller as read.",
    responses={
        401: {"description": "Authentication required"}
    }
)
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark all unread notifications as read.
    """
    db.query(Notification).filter(
        (Notification.recipient_id == current_user.id) |
        (Notification.recipient_role == current_user.role)
    ).update({"read": True})
    db.commit()
    return {"status": "all_marked_read"}

@router.post(
    "/outbox/process",
    response_model=OutboxProcessResponse,
    summary="Process Pending Outbox Messages",
    description="Triggers immediate delivery processing of queued outbox notifications using exponential backoff retry logic. Restricted to system administrators.",
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin sub-role required (system_admin)"}
    }
)
def process_outbox_queue(
    current_user: User = Depends(require_admin_sub_role(["system_admin"])),
    db: Session = Depends(get_db)
):
    """
    Triggers background processing of pending notifications in the outbox.
    """
    return notification_service.process_pending_outbox(db=db)

@router.get(
    "/outbox/status",
    response_model=OutboxStatusResponse,
    summary="Get Outbox Queue Metrics",
    description="Retrieves the current queue counts of pending, sent, and failed notifications in the transactional outbox table.",
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin sub-role required (system_admin)"}
    }
)
def get_outbox_status(
    current_user: User = Depends(require_admin_sub_role(["system_admin"])),
    db: Session = Depends(get_db)
):
    """
    Get outbox delivery metrics.
    """
    queued = db.query(NotificationOutbox).filter(NotificationOutbox.status == "queued").count()
    sent = db.query(NotificationOutbox).filter(NotificationOutbox.status == "sent").count()
    failed = db.query(NotificationOutbox).filter(NotificationOutbox.status == "failed").count()
    return {"queued": queued, "sent": sent, "failed": failed}
