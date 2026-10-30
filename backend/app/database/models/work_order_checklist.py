import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text
from app.database.base import Base

class WorkOrderChecklistItem(Base):
    __tablename__ = "work_order_checklist_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    work_order_id = Column(String(36), nullable=False, index=True)
    task_description = Column(String(255), nullable=False)
    step_order = Column(Integer, default=1, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    completed_by_id = Column(String(36), nullable=True)
    verification_notes = Column(Text, nullable=True)
    verification_status = Column(String(50), default="pending", nullable=False)  # pending, verified, rejected
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
