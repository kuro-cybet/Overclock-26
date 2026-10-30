import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from app.database.base import Base

class RoomBooking(Base):
    __tablename__ = "room_bookings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_code = Column(String(50), nullable=False, unique=True, index=True)
    room_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    user_role = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    purpose = Column(String(50), nullable=False)  # lecture, lab_session, examination, meeting, seminar
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), default="confirmed", nullable=False)  # confirmed, cancelled, relocated, completed
    equipment_required = Column(Text, nullable=True)  # JSON list
    conflict_resolved_to_room_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

