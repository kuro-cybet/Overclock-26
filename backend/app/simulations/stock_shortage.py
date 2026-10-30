import json
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database.models.inventory import InventoryItem
from app.database.models.work_order import WorkOrder
from app.database.models.approval import ApprovalRequest, ProcurementRequest
from app.services.inventory_service import inventory_service
from app.database.models.audit import AuditLog

class StockShortageSimulation:
    def trigger(self, db: Session, item_code: str = "INV-NET-007") -> Dict[str, Any]:
        item = db.query(InventoryItem).filter(InventoryItem.item_code == item_code).first()
        if not item:
            item = db.query(InventoryItem).first()

        # Find or create a work order requiring this part
        wo = db.query(WorkOrder).filter(WorkOrder.status.in_(["assigned", "in_progress"])).first()

        before_state = {
            "item_name": item.name,
            "stock_quantity": item.stock_quantity,
            "reserved_quantity": item.reserved_quantity,
            "available_quantity": item.available_quantity,
            "work_order_code": wo.work_order_code if wo else "N/A",
            "work_order_status": wo.status if wo else "N/A"
        }

        # 1. Force item stock to 0 if not already
        item.stock_quantity = 0
        item.reserved_quantity = 0

        # 2. Attempt reservation when stock is unavailable
        reservation_failed = False
        try:
            inventory_service.reserve_stock(db, work_order_id=wo.id if wo else "mock_wo", item_id=item.id, quantity=1)
        except Exception:
            reservation_failed = True

        # 3. Work order is blocked with clear blocked_reason
        if wo:
            wo.status = "blocked"
            wo.blocked_reason = f"Required part '{item.name}' unavailable in central store."

        # 4. Create emergency procurement request & approval request
        proc = ProcurementRequest(
            request_code=f"PRQ-EMERGENCY-{datetime.utcnow().strftime('%M%S')}",
            item_id=item.id,
            quantity=5,
            estimated_cost=item.unit_cost * 5,
            work_order_id=wo.id if wo else None,
            requester_id="admin-sim",
            status="requested"
        )
        db.add(proc)
        db.flush()

        app_req = ApprovalRequest(
            approval_type="purchase",
            target_entity_type="procurement",
            target_entity_id=proc.id,
            requester_id="admin-sim",
            status="pending",
            cost_amount=proc.estimated_cost,
            justification=f"Emergency restock of 5x {item.name} to unblock work order {wo.work_order_code if wo else ''}."
        )
        db.add(app_req)

        after_state = {
            "item_name": item.name,
            "stock_quantity": item.stock_quantity,
            "available_quantity": item.available_quantity,
            "reservation_blocked": reservation_failed,
            "work_order_status": wo.status if wo else "N/A",
            "work_order_blocked_reason": wo.blocked_reason if wo else "N/A",
            "procurement_request_code": proc.request_code,
            "pending_approval_id": app_req.id
        }

        # Audit
        audit = AuditLog(
            action="SIMULATION_STOCK_SHORTAGE",
            actor_id="admin-sim",
            actor_role="admin",
            entity_type="inventory",
            entity_id=item.id,
            old_value=json.dumps(before_state),
            new_value=json.dumps(after_state),
            reason="Scenario Simulator: Critical part out of stock attempted reservation"
        )
        db.add(audit)
        db.flush()

        return {
            "scenario": "critical_part_out_of_stock",
            "summary": f"Stock depleted for '{item.name}'. Reservation failed cleanly, Work Order blocked, Procurement Approval requested.",
            "before_state": before_state,
            "after_state": after_state,
            "pending_approval_id": app_req.id,
            "work_order_blocked": True
        }

stock_shortage_sim = StockShortageSimulation()

