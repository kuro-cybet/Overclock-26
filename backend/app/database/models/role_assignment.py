import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String

from app.database.base import Base


class RoleAssignmentFields:
    """
    Shared fields for the four role-specific Google sign-in allowlists.
    """

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    sub_role = Column(String(50), nullable=True)  # e.g. system_admin
    department = Column(String(100), nullable=True)
    building_id = Column(String(36), nullable=True)
    floor_id = Column(String(36), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    invited_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    consumed_at = Column(DateTime, nullable=True)


class AdminAssignment(RoleAssignmentFields, Base):
    __tablename__ = "admin_assignments"
    ROLE = "admin"


class TechnicianAssignment(RoleAssignmentFields, Base):
    __tablename__ = "technician_assignments"
    ROLE = "technician"


class FacultyAssignment(RoleAssignmentFields, Base):
    __tablename__ = "faculty_assignments"
    ROLE = "faculty"


class StudentAssignment(RoleAssignmentFields, Base):
    __tablename__ = "student_assignments"
    ROLE = "student"
