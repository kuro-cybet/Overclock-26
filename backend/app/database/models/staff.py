import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from app.database.base import Base

class StaffProfile(Base):
    __tablename__ = "staff_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, unique=True, index=True)
    skills = Column(Text, nullable=False)  # JSON serialized list of skills: ["network", "electrical", "hvac", "exam_setup"]
    shift = Column(String(50), nullable=False, default="morning")  # morning, evening, night
    assigned_building_id = Column(String(36), nullable=True)
    assigned_floor_id = Column(String(36), nullable=True)
    availability_status = Column(String(50), default="available", nullable=False)  # available, on_task, absent, on_leave
    current_workload = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
