import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime
from app.database.base import Base

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = Column(String(36), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False, index=True)  # intake, reservation_hold, consumption, release, adjustment, procurement_receipt
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Float, default=0.0, nullable=False)
    work_order_id = Column(String(36), nullable=True, index=True)
    actor_id = Column(String(36), nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
