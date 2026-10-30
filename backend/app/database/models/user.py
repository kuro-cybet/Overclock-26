import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from app.database.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    # Google OAuth accounts have no password; the column stays NOT NULL for the
    # tracked SQLite schema, so they get the sentinel "!" which never verifies.
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, index=True)  # admin, technician, faculty, student
    sub_role = Column(String(50), nullable=True)  # e.g., facilities_admin, maintenance_technician
    department = Column(String(100), nullable=True)
    building_id = Column(String(36), nullable=True)
    floor_id = Column(String(36), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    auth_provider = Column(String(20), default="password", nullable=True)  # password | google
    provider_subject = Column(String(255), nullable=True, index=True)  # Google `sub`
    email_verified = Column(Boolean, default=False, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    phone_number = Column(String(30), unique=True, nullable=True, index=True)
    whatsapp_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
