import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Text
from app.database.base import Base

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    approval_type = Column(String(50), nullable=False)  # purchase, costly_repair, room_override, reassignment
    target_entity_type = Column(String(50), nullable=False)  # procurement, work_order, room, staff
    target_entity_id = Column(String(36), nullable=False, index=True)
    requester_id = Column(String(36), nullable=False, index=True)
    approver_id = Column(String(36), nullable=True, index=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, approved, rejected
    cost_amount = Column(Float, default=0.0, nullable=False)
    justification = Column(Text, nullable=False)
    decision_reason = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class ProcurementRequest(Base):
    __tablename__ = "procurement_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_code = Column(String(50), nullable=False, unique=True, index=True)
    item_id = Column(String(36), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    estimated_cost = Column(Float, nullable=False)
    work_order_id = Column(String(36), nullable=True, index=True)
    requester_id = Column(String(36), nullable=False, index=True)
    status = Column(String(50), default="requested", nullable=False)  # requested, approved, ordered, received, rejected
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

