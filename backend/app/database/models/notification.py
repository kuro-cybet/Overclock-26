import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text
from app.database.base import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_id = Column(String(36), nullable=False, index=True)
    recipient_role = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info", nullable=False)  # info, warning, critical, action_required
    read = Column(Boolean, default=False, nullable=False)
    link_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class NotificationOutbox(Base):
    __tablename__ = "notification_outbox"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_email = Column(String(255), nullable=False)
    channel = Column(String(50), default="email", nullable=False)  # email, in_app, webhook
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(50), default="queued", nullable=False)  # queued, processing, sent, failed
    attempts = Column(Integer, default=0, nullable=False)
    last_attempt_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

