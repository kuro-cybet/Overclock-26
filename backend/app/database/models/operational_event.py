import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from app.database.base import Base

class OperationalEvent(Base):
    __tablename__ = "operational_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(100), nullable=False, index=True)
    # Types: incident_created, incident_classified, technician_assigned, work_order_blocked,
    # stock_reserved, stock_consumed, approval_requested, approval_completed,
    # room_booking_changed, recovery_started, recovery_completed, recovery_verified, sla_breached, asset_degraded

    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    severity = Column(String(20), default="info", nullable=False)  # info, warning, critical, emergency
    payload_json = Column(Text, nullable=True)
    actor_id = Column(String(36), nullable=True)
    acknowledged = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
