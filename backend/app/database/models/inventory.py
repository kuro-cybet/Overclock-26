import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime
from app.database.base import Base

class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    item_code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)  # network, electrical, hardware, plumbing, general
    stock_quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    unit_cost = Column(Float, default=0.0, nullable=False)
    minimum_threshold = Column(Integer, default=5, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    @property
    def available_quantity(self) -> int:
        return max(0, self.stock_quantity - self.reserved_quantity)

class StockReservation(Base):
    __tablename__ = "stock_reservations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    work_order_id = Column(String(36), nullable=False, index=True)
    item_id = Column(String(36), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    status = Column(String(50), default="reserved", nullable=False)  # reserved, consumed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

