import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.database.base import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_tag = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)  # network, av_equipment, hvac, electrical, furniture, lab_equipment
    building_id = Column(String(36), nullable=False, index=True)
    room_id = Column(String(36), nullable=False, index=True)
    status = Column(String(50), default="operational", nullable=False)  # operational, degraded, inoperable, maintenance
    serial_number = Column(String(100), nullable=True)
    last_inspected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
