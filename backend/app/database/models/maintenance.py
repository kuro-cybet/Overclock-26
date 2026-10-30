import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean
from app.database.base import Base

class AssetMaintenanceHistory(Base):
    __tablename__ = "asset_maintenance_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String(36), nullable=False, index=True)
    work_order_id = Column(String(36), nullable=True, index=True)
    maintenance_type = Column(String(50), nullable=False)  # preventive, corrective, emergency, inspection
    findings = Column(Text, nullable=True)
    actions_taken = Column(Text, nullable=True)
    replaced_parts_json = Column(Text, nullable=True)
    cost = Column(Float, default=0.0, nullable=False)
    performed_by_id = Column(String(36), nullable=True)
    completed_at = Column(DateTime, nullable=True)

class PreventiveMaintenanceSchedule(Base):
    __tablename__ = "preventive_maintenance_schedules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String(36), nullable=True, index=True)
    schedule_name = Column(String(150), nullable=False)
    frequency_days = Column(Integer, default=30, nullable=False)
    last_performed_at = Column(DateTime, nullable=True)
    next_due_at = Column(DateTime, nullable=False, index=True)
    checklist_template = Column(Text, nullable=True)
    priority = Column(String(20), default="medium", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
