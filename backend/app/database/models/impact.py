import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from app.database.base import Base

class IncidentImpactRecord(Base):
    __tablename__ = "incident_impact_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), nullable=False, unique=True, index=True)
    affected_rooms_count = Column(Integer, default=0, nullable=False)
    affected_classes_count = Column(Integer, default=0, nullable=False)
    estimated_students_affected = Column(Integer, default=0, nullable=False)
    exams_at_risk = Column(Integer, default=0, nullable=False)
    financial_impact_estimate = Column(Float, default=0.0, nullable=False)
    severity_score = Column(Float, default=50.0, nullable=False)
    impact_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
