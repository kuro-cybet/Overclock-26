import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from app.database.base import Base

class Building(Base):
    __tablename__ = "buildings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(150), nullable=False, unique=True)
    code = Column(String(20), nullable=False, unique=True)
    total_floors = Column(Integer, default=3, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Floor(Base):
    __tablename__ = "floors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    building_id = Column(String(36), nullable=False, index=True)
    floor_number = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
