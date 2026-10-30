import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean
from app.database.base import Base

class HistoricalResolution(Base):
    __tablename__ = "historical_resolutions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category = Column(String(50), nullable=False, index=True)
    asset_id = Column(String(36), nullable=True, index=True)
    room_id = Column(String(36), nullable=True, index=True)
    symptoms = Column(Text, nullable=False)
    diagnosis = Column(Text, nullable=False)
    action_taken = Column(Text, nullable=False)
    parts_used = Column(Text, nullable=True)  # JSON list
    resolution_duration_minutes = Column(Integer, default=60, nullable=False)
    verified_outcome = Column(String(100), default="successful_operational_recovery", nullable=False)
    source_work_order_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class PredictiveAlert(Base):
    __tablename__ = "predictive_alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_type = Column(String(50), nullable=False, index=True)  # sla_risk, repeated_failure, stock_shortage, readiness_gap
    affected_entity_type = Column(String(50), nullable=False)  # incident, asset, item, room
    affected_entity_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    evidence_refs = Column(Text, nullable=False)  # Description / stats backing the claim
    trigger_threshold = Column(String(100), nullable=False)
    predicted_window = Column(String(100), nullable=True)  # e.g. "Next 2 hours"
    confidence = Column(Float, default=0.85, nullable=False)
    status = Column(String(50), default="active", nullable=False)  # active, mitigated, dismissed
    deduplication_key = Column(String(120), nullable=False, unique=True, index=True)
    recommended_action = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

