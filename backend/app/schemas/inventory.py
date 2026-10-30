from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class InventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_code: str
    name: str
    category: str
    stock_quantity: int
    reserved_quantity: int
    unit_cost: float
    minimum_threshold: int
    created_at: datetime

class InventoryReserveRequest(BaseModel):
    work_order_id: str
    item_id: str
    quantity: int

class InventoryReserveResponse(BaseModel):
    status: str
    reservation_id: str
    quantity: int

class StockReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    work_order_id: str
    item_id: str
    quantity: int
    status: str
    created_at: datetime

class ProcurementCreateRequest(BaseModel):
    item_id: str
    quantity: int
    work_order_id: Optional[str] = None
    justification: Optional[str] = "Replenishment for blocked operational work order"

class ProcurementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    request_code: str
    item_id: str
    quantity: int
    estimated_cost: float
    work_order_id: Optional[str] = None
    requester_id: str
    status: str
    created_at: datetime

class ProcurementCreateResponse(BaseModel):
    procurement_request: ProcurementResponse
    approval_request_id: str
