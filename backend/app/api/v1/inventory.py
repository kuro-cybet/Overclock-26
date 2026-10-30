from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.inventory import InventoryItem, StockReservation
from app.schemas.inventory import (
    InventoryResponse,
    InventoryReserveRequest,
    InventoryReserveResponse
)
from app.services.inventory_service import inventory_service
from app.core.exceptions import EntityNotFoundError

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.get(
    "",
    response_model=List[InventoryResponse],
    summary="List Inventory Items",
    description="Retrieves spare parts, tools, and consumable materials available in campus central stores with real-time stock and reservation counts."
)
def list_inventory(
    category: Optional[str] = Query(None, description="Filter by category: `electrical`, `hvac`, `plumbing`, `network`, `hardware`, `consumables`"),
    limit: int = Query(100, ge=1, le=500, description="Maximum items to return"),
    db: Session = Depends(get_db)
):
    """
    List spare parts inventory items with minimum threshold indicators.
    """
    q = db.query(InventoryItem)
    if category:
        q = q.filter(InventoryItem.category == category)
    items = q.limit(limit).all()
    return items

@router.get(
    "/{item_id}",
    response_model=InventoryResponse,
    summary="Get Inventory Item by ID",
    description="Retrieves details, unit cost, available stock, and minimum safety threshold for an inventory item.",
    responses={
        404: {"description": "Inventory item not found"}
    }
)
def get_inventory_item(item_id: str, db: Session = Depends(get_db)):
    """
    Retrieve single inventory item record.
    """
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise EntityNotFoundError("InventoryItem", item_id)
    return item

@router.post(
    "/reserve",
    response_model=InventoryReserveResponse,
    summary="Reserve Inventory Stock for Work Order",
    description="Atomically creates a stock reservation hold against available inventory without decreasing total stock on hand. Prevents over-reservation.",
    responses={
        404: {"description": "Inventory item or work order not found"},
        409: {"description": "Over-reservation: Requested quantity exceeds available unreserved stock"}
    }
)
def reserve_stock(
    payload: InventoryReserveRequest,
    db: Session = Depends(get_db)
):
    """
    Atomically reserve spare parts for work order execution.
    """
    res = inventory_service.reserve_stock(
        db=db,
        work_order_id=payload.work_order_id,
        item_id=payload.item_id,
        quantity=payload.quantity
    )
    db.commit()
    return {
        "status": "reserved",
        "reservation_id": res.id,
        "quantity": res.quantity
    }
