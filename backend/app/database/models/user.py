import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from app.database.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, index=True)  # admin, technician, faculty, student
    sub_role = Column(String(50), nullable=True)  # e.g., facilities_admin, maintenance_technician
    department = Column(String(100), nullable=True)
    building_id = Column(String(36), nullable=True)
    floor_id = Column(String(36), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
