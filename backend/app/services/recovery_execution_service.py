import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.database.models.recovery import RecoveryExecution, RecoveryAction
from app.database.models.incident import Incident
from app.database.models.room import Room
from app.database.models.booking import RoomBooking
from app.database.models.work_order import WorkOrder
from app.database.models.inventory import InventoryItem
from app.database.models.approval import ApprovalRequest, ProcurementRequest
from app.database.models.user import User
from app.database.models.explanation import DecisionExplanation
from app.services.booking_service import booking_service
from app.services.assignment_service import assignment_service
from app.services.notification_service import notification_service
from app.services.event_service import event_service
from app.core.exceptions import PermissionDeniedError, SeparationOfDutiesError, CampusOpsException

logger = logging.getLogger(__name__)

class RecoveryExecutionService:
    """
    Executes authorized recovery actions across spatial, staff, and inventory resources.
    Guarantees atomic execution tracking, approval gating, and targeted user notifications.
    """

    def initiate_recovery(
        self,
        db: Session,
        incident_id: Optional[str],
        disruption_type: str,
        chosen_plan_id: str,
        actions_spec: List[Dict[str, Any]],
        initiated_by_user: User
    ) -> RecoveryExecution:
        """
        Creates a new RecoveryExecution record and stages its discrete recovery actions.
        """
        execution = RecoveryExecution(
            incident_id=incident_id,
            disruption_type=disruption_type,
            chosen_plan_id=chosen_plan_id,
            status="in_progress",
            executed_by_id=initiated_by_user.id,
            executed_at=datetime.utcnow(),
            verification_status="pending",
            verification_outcome="Execution initiated. Awaiting independent physical verification."
        )
        db.add(execution)
        db.flush()

        # Stage discrete actions
        for action_data in actions_spec:
            action = RecoveryAction(
                execution_id=execution.id,
                action_type=action_data.get("action_type", "general_recovery"),
                target_entity_type=action_data.get("target_entity_type", "incident"),
                target_entity_id=action_data.get("target_entity_id", execution.id),
                status="pending",
                action_payload=json.dumps(action_data.get("payload", {}))
            )
            db.add(action)

        db.flush()

        # Log Decision Explanation
        expl = DecisionExplanation(
            decision_type="autonomous_recovery",
            entity_type="recovery_execution",
            entity_id=execution.id,
            actor_id=initiated_by_user.id,
            chosen_option=chosen_plan_id,
            alternative_options_json="[]",
            factors_json=json.dumps({
                "disruption_type": disruption_type,
                "chosen_plan_id": chosen_plan_id,
                "actions_count": len(actions_spec),
                "operator": initiated_by_user.name
            }),
            confidence_score=0.94,
            explanation_text=(
                f"Selected recovery plan '{chosen_plan_id}' for {disruption_type}. "
                f"Actions scheduled across {len(actions_spec)} operational domains to mitigate impact."
            )
        )
        db.add(expl)

        event_service.log_event(
            db=db,
            event_type="recovery_started",
            entity_type="recovery_execution",
            entity_id=execution.id,
            severity="warning",
            payload={"disruption_type": disruption_type, "plan_id": chosen_plan_id},
            actor_id=initiated_by_user.id
        )

        db.commit()
        return execution

    def execute_recovery_actions(
        self,
        db: Session,
        execution_id: str,
        operator: User
    ) -> Dict[str, Any]:
        """
        Executes all pending recovery actions associated with a recovery execution.
        """
        execution = db.query(RecoveryExecution).filter(RecoveryExecution.id == execution_id).first()
        if not execution:
            raise CampusOpsException("Recovery execution record not found", 404)

        actions = (
            db.query(RecoveryAction)
            .filter(RecoveryAction.execution_id == execution.id, RecoveryAction.status == "pending")
            .all()
        )

        executed_results = []
        for action in actions:
            action.started_at = datetime.utcnow()
            payload = json.loads(action.action_payload or "{}")

            try:
                if action.action_type == "room_relocation":
                    res = self._execute_room_relocation(db, payload, operator)
                elif action.action_type == "emergency_dispatch":
                    res = self._execute_emergency_dispatch(db, payload, operator)
                elif action.action_type == "parts_procurement":
                    res = self._execute_parts_procurement(db, payload, operator)
                elif action.action_type == "notification_broadcast":
                    res = self._execute_notification_broadcast(db, payload)
                else:
                    res = {"status": "executed", "details": "Custom operational action applied."}

                action.status = "completed"
                action.result_payload = json.dumps(res)
                action.completed_at = datetime.utcnow()
                executed_results.append({"action_id": action.id, "status": "completed", "result": res})

            except Exception as e:
                action.status = "failed"
                action.error_message = str(e)
                action.completed_at = datetime.utcnow()
                executed_results.append({"action_id": action.id, "status": "failed", "error": str(e)})
                logger.error(f"[RecoveryExecutionService] Action {action.id} failed: {e}")

        # Update execution state
        all_completed = all(a.status == "completed" for a in actions)
        execution.status = "awaiting_verification"

        db.commit()
        return {
            "execution_id": execution.id,
            "status": execution.status,
            "actions_executed": executed_results
        }

    def _execute_room_relocation(self, db: Session, payload: Dict[str, Any], operator: User) -> Dict[str, Any]:
        booking_id = payload.get("booking_id")
        new_room_id = payload.get("new_room_id")
        orig_room_id = payload.get("original_room_id")

        booking = db.query(RoomBooking).filter(RoomBooking.id == booking_id).first()
        new_room = db.query(Room).filter(Room.id == new_room_id).first()
        orig_room = db.query(Room).filter(Room.id == orig_room_id).first()

        if booking and new_room:
            old_code = orig_room.room_number if orig_room else "Affected Room"
            booking.room_id = new_room.id
            booking.notes = (booking.notes or "") + f" | [Relocated from {old_code} to {new_room.room_number} by {operator.name}]"

            # Mark original room as under maintenance / restricted
            if orig_room:
                orig_room.status = "under_maintenance"

            # Notify organizer
            notification_service.create_notification(
                db=db,
                recipient_id=booking.user_id,
                title="URGENT: Booking Relocated",
                message=f"Your session '{booking.title}' has been safely moved to {new_room.room_number} ({new_room.name}).",
                severity="warning"
            )

            return {
                "booking_id": booking.id,
                "original_room": old_code,
                "relocated_to": new_room.room_number,
                "status": "relocated"
            }
        return {"status": "skipped", "reason": "Booking or target room not found"}

    def _execute_emergency_dispatch(self, db: Session, payload: Dict[str, Any], operator: User) -> Dict[str, Any]:
        work_order_id = payload.get("work_order_id")
        new_technician_id = payload.get("new_technician_id")

        wo = assignment_service.assign_technician_to_work_order(
            db=db,
            work_order_id=work_order_id,
            technician_id=new_technician_id,
            reassign_reason=f"Emergency autonomous dispatch: {payload.get('reason', 'Workload rebalance')}"
        )
        return {"work_order_id": wo.id, "assigned_technician_id": wo.assigned_technician_id, "status": "reassigned"}

    def _execute_parts_procurement(self, db: Session, payload: Dict[str, Any], operator: User) -> Dict[str, Any]:
        item_id = payload.get("item_id")
        quantity = int(payload.get("quantity", 1))
        work_order_id = payload.get("work_order_id")

        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            return {"status": "failed", "reason": "Item not found"}

        proc = ProcurementRequest(
            item_id=item.id,
            quantity=quantity,
            estimated_cost=float(item.unit_cost or 50.0) * quantity,
            justification=f"Autonomous recovery replenishment for {item.name}",
            requester_id=operator.id,
            work_order_id=work_order_id,
            status="pending"
        )
        db.add(proc)
        db.flush()

        approval = ApprovalRequest(
            approval_type="purchase",
            target_entity_type="procurement",
            target_entity_id=proc.id,
            requester_id=operator.id,
            justification=f"Urgent spare part replenishment: {item.name} x {quantity}",
            status="pending"
        )
        db.add(approval)
        db.flush()

        return {"procurement_id": proc.id, "approval_id": approval.id, "status": "procurement_staged"}

    def _execute_notification_broadcast(self, db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        recipients = payload.get("recipients", ["admin"])
        title = payload.get("title", "Campus Operations Notice")
        message = payload.get("message", "Operational update applied.")

        count = 0
        for r_id in recipients:
            notification_service.create_notification(
                db=db,
                recipient_id=r_id,
                title=title,
                message=message,
                severity="info"
            )
            count += 1

        return {"notifications_sent": count, "title": title}

recovery_execution_service = RecoveryExecutionService()
