from sqlalchemy.orm import Session
from app.database.models.inventory import InventoryItem, StockReservation
from app.database.models.work_order import WorkOrder
from app.core.exceptions import StockUnavailableError, CampusOpsException

class InventoryService:
    def reserve_stock(
        self,
        db: Session,
        work_order_id: str,
        item_id: str,
        quantity: int
    ) -> StockReservation:
        # Atomic lock/check on inventory item
        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).with_for_update().first()
        if not item:
            raise CampusOpsException(f"Inventory item '{item_id}' not found.", 404)

        available = item.available_quantity
        if available < quantity:
            # Block work order if linked
            wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
            if wo:
                wo.status = "blocked"
                wo.blocked_reason = f"Required part '{item.name}' out of stock (Available: {available}, Required: {quantity})"
                db.flush()

            raise StockUnavailableError(item_name=item.name, requested=quantity, available=available)

        # Increment reserved quantity transactionally
        item.reserved_quantity += quantity

        reservation = StockReservation(
            work_order_id=work_order_id,
            item_id=item_id,
            quantity=quantity,
            status="reserved"
        )
        db.add(reservation)
        db.flush()
        return reservation

    def consume_stock(
        self,
        db: Session,
        reservation_id: str
    ):
        res = db.query(StockReservation).filter(StockReservation.id == reservation_id).first()
        if not res or res.status != "reserved":
            raise CampusOpsException("Valid active stock reservation required for consumption.", 400)

        item = db.query(InventoryItem).filter(InventoryItem.id == res.item_id).with_for_update().first()
        if item:
            item.stock_quantity = max(0, item.stock_quantity - res.quantity)
            item.reserved_quantity = max(0, item.reserved_quantity - res.quantity)

        res.status = "consumed"
        db.flush()

inventory_service = InventoryService()

