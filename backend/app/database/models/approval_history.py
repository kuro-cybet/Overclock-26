import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from app.database.base import Base

class ApprovalHistory(Base):
    __tablename__ = "approval_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    approval_request_id = Column(String(36), nullable=False, index=True)
    stage = Column(String(50), nullable=False)  # submission, department_review, procurement_review, completed
    action = Column(String(50), nullable=False)  # submitted, approved, rejected, escalated, reassigned
    actor_id = Column(String(36), nullable=True)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
