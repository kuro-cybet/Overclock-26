import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from app.database.base import Base

class TransportRoute(Base):
    __tablename__ = "transport_routes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    route_number = Column(String(50), nullable=False, unique=True, index=True)  # e.g., "RT-01", "RT-02"
    route_name = Column(String(150), nullable=False)  # e.g., "Tambaram - Campus Express"
    origin = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False, default="Campus Main Gate")
    vehicle_number = Column(String(50), nullable=False)  # e.g., "TN-01-CP-4521"
    driver_name = Column(String(100), nullable=False)
    driver_phone = Column(String(30), nullable=False)
    capacity = Column(Integer, default=50, nullable=False)
    operating_days = Column(String(50), default="Mon-Sat", nullable=False)
    status = Column(String(30), default="active", nullable=False)  # active, delayed, maintenance, cancelled
    announcement = Column(Text, nullable=True)
    is_published = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class TransportStop(Base):
    __tablename__ = "transport_stops"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    route_id = Column(String(36), nullable=False, index=True)
    stop_name = Column(String(100), nullable=False, index=True)  # e.g., "Tambaram Sanatorium", "Chromepet"
    sequence_order = Column(Integer, nullable=False, default=1)
    pickup_time = Column(String(20), nullable=False)  # e.g., "07:15 AM"
    drop_time = Column(String(20), nullable=False)    # e.g., "05:45 PM"
    landmark = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class TransportAllocation(Base):
    __tablename__ = "transport_allocations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    route_id = Column(String(36), nullable=False, index=True)
    stop_id = Column(String(36), nullable=False, index=True)
    academic_year = Column(String(20), default="2026-2027", nullable=False)
    status = Column(String(20), default="active", nullable=False)  # active, inactive
    fee_status = Column(String(20), default="paid", nullable=False)  # paid, pending, exempt
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class TransportAnnouncement(Base):
    __tablename__ = "transport_announcements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    route_id = Column(String(36), nullable=True, index=True)  # None = Broadcast across all campus routes
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), default="normal", nullable=False)  # normal, urgent
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

