import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from app.database.base import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_code = Column(String(50), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    severity = Column(String(50), nullable=False, default="medium")  # low, medium, high, critical
    priority = Column(String(10), nullable=False, default="P3")  # P1, P2, P3, P4
    building_id = Column(String(36), nullable=False, index=True)
    room_id = Column(String(36), nullable=True, index=True)
    asset_id = Column(String(36), nullable=True, index=True)
    status = Column(String(50), default="open", nullable=False)  # open, in_progress, pending_parts, pending_approval, resolved, closed
    sla_due_at = Column(DateTime, nullable=True)
    is_sla_breached = Column(Boolean, default=False, nullable=False)
    correlated_count = Column(Integer, default=1, nullable=False)
    summary = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
