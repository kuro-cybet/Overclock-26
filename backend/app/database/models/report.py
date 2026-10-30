import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from app.database.base import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_code = Column(String(50), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # network, classroom, electrical, cleanliness, safety, equipment
    urgency = Column(String(50), nullable=False, default="medium")  # low, medium, high, critical
    building_id = Column(String(36), nullable=False, index=True)
    room_id = Column(String(36), nullable=True, index=True)
    asset_id = Column(String(36), nullable=True, index=True)
    reporter_id = Column(String(36), nullable=False, index=True)
    reporter_role = Column(String(50), nullable=False)  # student, faculty, admin, technician
    source = Column(String(50), default="web_portal", nullable=False)  # web_portal, simulated_email, mobile
    status = Column(String(50), default="submitted", nullable=False)  # submitted, triaged, correlated, resolved, rejected
    incident_id = Column(String(36), nullable=True, index=True)
    ai_extracted_meta = Column(Text, nullable=True)  # JSON metadata from AI extractor
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
