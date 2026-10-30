from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.inventory import InventoryItem, StockReservation
from app.schemas.inventory import InventoryResponse, InventoryReserveRequest
from app.services.inventory_service import inventory_service
from app.core.exceptions import EntityNotFoundError

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.get("", response_model=List[InventoryResponse])
def list_inventory(
    category: Optional[str] = Query(None),
    limit: int = 100,
    db: Session = Depends(get_db)
):
    q = db.query(InventoryItem)
    if category:
        q = q.filter(InventoryItem.category == category)
    items = q.limit(limit).all()
    return items

@router.get("/{item_id}", response_model=InventoryResponse)
def get_inventory_item(item_id: str, db: Session = Depends(get_db)):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise EntityNotFoundError("InventoryItem", item_id)
    return item

@router.post("/reserve")
def reserve_stock(
    payload: InventoryReserveRequest,
    db: Session = Depends(get_db)
):
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

