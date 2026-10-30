import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from app.database.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action = Column(String(100), nullable=False, index=True)
    actor_id = Column(String(36), nullable=False, index=True)
    actor_role = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    old_value = Column(Text, nullable=True)  # JSON representation
    new_value = Column(Text, nullable=True)  # JSON representation
    reason = Column(Text, nullable=True)
    ip_address = Column(String(50), default="127.0.0.1")
    idempotency_key = Column(String(100), nullable=True, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

