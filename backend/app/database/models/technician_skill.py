import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from app.database.base import Base

class Skill(Base):
    __tablename__ = "skills"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class TechnicianSkill(Base):
    __tablename__ = "technician_skills"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    technician_id = Column(String(36), nullable=False, index=True)
    skill_id = Column(String(36), nullable=False, index=True)
    proficiency_level = Column(String(20), default="intermediate", nullable=False)  # beginner, intermediate, advanced, expert
    certified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class WorkOrderSkillRequirement(Base):
    __tablename__ = "work_order_skill_requirements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    work_order_id = Column(String(36), nullable=False, index=True)
    skill_id = Column(String(36), nullable=False, index=True)
    min_proficiency = Column(String(20), default="intermediate", nullable=False)
    is_mandatory = Column(Boolean, default=True, nullable=False)
