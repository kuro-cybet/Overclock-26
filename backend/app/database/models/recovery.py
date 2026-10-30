import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from app.database.base import Base

class RecoveryExecution(Base):
    __tablename__ = "recovery_executions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), nullable=True, index=True)
    disruption_type = Column(String(100), nullable=False, index=True)
    chosen_plan_id = Column(String(50), nullable=True)
    status = Column(String(50), default="proposed", nullable=False)  # proposed, approved, in_progress, verified_success, verification_failed, cancelled
    executed_by_id = Column(String(36), nullable=True)
    executed_at = Column(DateTime, nullable=True)
    verification_status = Column(String(50), default="pending", nullable=False)  # pending, verified_success, verification_failed
    verification_outcome = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id = Column(String(36), nullable=False, index=True)
    action_type = Column(String(100), nullable=False)  # room_relocation, emergency_dispatch, parts_procurement, notification_broadcast, override_signoff
    target_entity_type = Column(String(50), nullable=False)
    target_entity_id = Column(String(36), nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, executing, completed, failed
    action_payload = Column(Text, nullable=True)
    result_payload = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
