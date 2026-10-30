from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.notification import Notification
from app.database.models.user import User
from app.schemas.notification import NotificationResponse
from app.core.exceptions import EntityNotFoundError
from app.api.deps import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("", response_model=List[NotificationResponse])
def get_user_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifs = db.query(Notification).filter(
        (Notification.recipient_id == current_user.id) |
        (Notification.recipient_role == current_user.role)
    ).order_by(Notification.created_at.desc()).limit(30).all()
    return notifs

@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise EntityNotFoundError("Notification", notification_id)
    notif.read = True
    db.commit()
    db.refresh(notif)
    return notif

@router.post("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(
        (Notification.recipient_id == current_user.id) |
        (Notification.recipient_role == current_user.role)
    ).update({"read": True})
    db.commit()
    return {"status": "all_marked_read"}

