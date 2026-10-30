import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from app.database.base import Base

class Room(Base):
    __tablename__ = "rooms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    building_id = Column(String(36), nullable=False, index=True)
    floor_id = Column(String(36), nullable=False, index=True)
    room_number = Column(String(50), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    type = Column(String(50), nullable=False)  # classroom, lab, exam_hall, seminar_hall, etc.
    capacity = Column(Integer, nullable=False, default=40)
    features = Column(Text, nullable=True)  # JSON serialized list of features e.g. ["projector", "ac", "lab_pcs"]
    status = Column(String(50), default="available", nullable=False)  # available, occupied, under_maintenance, unavailable
    
    # Freshness-aware attributes (Upgrade Section 3A & 6)
    daily_readiness_status = Column(String(50), default="unconfirmed", nullable=False)
    freshness_state = Column(String(50), default="unconfirmed", nullable=False)  # confirmed_today, carried_forward, stale, unconfirmed, unavailable
    last_confirmed_at = Column(DateTime, nullable=True)
    confirmed_by = Column(String(100), nullable=True)
    freshness_source = Column(String(50), default="daily_inspection")  # daily_inspection, sensor, admin_override
    
    readiness_checked_at = Column(DateTime, nullable=True)
    readiness_checked_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
