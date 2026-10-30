from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class InventoryResponse(BaseModel):
    id: str
    item_code: str
    name: str
    category: str
    stock_quantity: int
    reserved_quantity: int
    unit_cost: float
    minimum_threshold: int
    created_at: datetime

    class Config:
        from_attributes = True

class InventoryReserveRequest(BaseModel):
    work_order_id: str
    item_id: str
    quantity: int

class ProcurementCreateRequest(BaseModel):
    item_id: str
    quantity: int
    work_order_id: Optional[str] = None
    justification: Optional[str] = "Replenishment for blocked operational work order"

