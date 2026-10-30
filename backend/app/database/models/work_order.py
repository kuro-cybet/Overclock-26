import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from app.database.base import Base

class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    work_order_code = Column(String(50), nullable=False, unique=True, index=True)
    incident_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    assigned_technician_id = Column(String(36), nullable=True, index=True)
    priority = Column(String(10), nullable=False, default="P3")  # P1, P2, P3, P4
    status = Column(String(50), default="assigned", nullable=False)  # assigned, in_progress, blocked, pending_parts, completed, cancelled
    required_skills = Column(Text, nullable=True)  # JSON list
    sla_deadline = Column(DateTime, nullable=True)
    blocked_reason = Column(String(255), nullable=True)
    diagnosis = Column(Text, nullable=True)
    checklist = Column(Text, nullable=True)  # JSON list of tasks
    evidence_notes = Column(Text, nullable=True)
    
    # Historical & resolution context (Upgrade Section 4 #5)
    matched_historical_case_id = Column(String(36), nullable=True)
    historical_resolution_summary = Column(Text, nullable=True)

    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
