import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String

from app.database.base import Base


class RoleAssignment(Base):
    """
    Server-side RBAC allowlist.

    A person is only granted a role if their verified email exists here. The
    Google OAuth callback never accepts a role from the client; it looks the
    role up from this table, then provisions/updates the matching ``users`` row.
    """

    __tablename__ = "role_assignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(String(50), nullable=False)  # admin, technician, faculty, student
    sub_role = Column(String(50), nullable=True)  # e.g. system_admin
    department = Column(String(100), nullable=True)
    building_id = Column(String(36), nullable=True)
    floor_id = Column(String(36), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    invited_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    consumed_at = Column(DateTime, nullable=True)
