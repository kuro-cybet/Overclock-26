import logging
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.database.models.recovery import RecoveryExecution
from app.database.models.incident import Incident
from app.database.models.work_order import WorkOrder
from app.database.models.room import Room
from app.database.models.work_order_checklist import WorkOrderChecklistItem
from app.database.models.user import User
from app.services.event_service import event_service
from app.core.exceptions import CampusOpsException

logger = logging.getLogger(__name__)

class RecoveryVerificationService:
    """
    Independent Verification Engine for CampusOps.
    Strictly verifies physical restoration and diagnostic evidence
    BEFORE permitting any incident or recovery plan to be marked 'resolved'.
    """

    def verify_recovery_execution(
        self,
        db: Session,
        execution_id: str,
        inspector_user: User
    ) -> Dict[str, Any]:
        """
        Runs independent multi-point validation on a recovery execution.
        """
        execution = db.query(RecoveryExecution).filter(RecoveryExecution.id == execution_id).first()
        if not execution:
            raise CampusOpsException("Recovery execution record not found", 404)

        checks_passed = []
        checks_failed = []

        # Check 1: Verify linked Incident & Work Orders
        incident = None
        if execution.incident_id:
            incident = db.query(Incident).filter(Incident.id == execution.incident_id).first()

        if incident:
            work_orders = db.query(WorkOrder).filter(WorkOrder.incident_id == incident.id).all()
            for wo in work_orders:
                # Check status
                if wo.status != "completed":
                    checks_failed.append(f"Work order {wo.work_order_code} is still '{wo.status}', not completed.")
                else:
                    checks_passed.append(f"Work order {wo.work_order_code} status is completed.")

                # Check checklist completion
                checklist_items = (
                    db.query(WorkOrderChecklistItem)
                    .filter(WorkOrderChecklistItem.work_order_id == wo.id)
                    .all()
                )
                if checklist_items:
                    incomplete = [item.task_description for item in checklist_items if not item.is_completed]
                    if incomplete:
                        checks_failed.append(f"{wo.work_order_code} has {len(incomplete)} incomplete mandatory checklist step(s): {', '.join(incomplete[:2])}")
                    else:
                        checks_passed.append(f"All {len(checklist_items)} checklist items signed-off for {wo.work_order_code}.")

                # Check evidence notes
                if not wo.evidence_notes or len(wo.evidence_notes.strip()) < 5:
                    checks_failed.append(f"{wo.work_order_code} lacks required physical evidence notes / diagnostic sign-off.")
                else:
                    checks_passed.append(f"Physical evidence notes confirmed for {wo.work_order_code}.")

            # Check 2: Verify Room physical restoration
            if incident.room_id:
                room = db.query(Room).filter(Room.id == incident.room_id).first()
                if room:
                    if room.status not in ["operational", "available"]:
                        checks_failed.append(f"Room {room.room_number} condition is '{room.status}', not operational.")
                    else:
                        checks_passed.append(f"Room {room.room_number} operational state confirmed.")

        # Determine overall verification outcome
        execution.verified_at = datetime.utcnow()
        is_success = len(checks_failed) == 0

        if is_success:
            execution.verification_status = "verified_success"
            execution.status = "verified_success"
            execution.verification_outcome = (
                f"Physical verification passed by {inspector_user.name}. "
                f"All checks confirmed: {'; '.join(checks_passed)}"
            )

            # Safely transition incident to resolved
            if incident and incident.status != "resolved":
                incident.status = "resolved"
                incident.resolved_at = datetime.utcnow()

            event_service.log_event(
                db=db,
                event_type="recovery_verified",
                entity_type="recovery_execution",
                entity_id=execution.id,
                severity="info",
                payload={"outcome": "verified_success", "checks": checks_passed},
                actor_id=inspector_user.id
            )
        else:
            execution.verification_status = "verification_failed"
            execution.status = "verification_failed"
            execution.verification_outcome = (
                f"Physical verification FAILED by {inspector_user.name}. "
                f"Issues preventing closure: {'; '.join(checks_failed)}"
            )

            # Prevent incident closure; keep in_progress
            if incident:
                incident.status = "in_progress"

            event_service.log_event(
                db=db,
                event_type="recovery_verification_failed",
                entity_type="recovery_execution",
                entity_id=execution.id,
                severity="critical",
                payload={"outcome": "verification_failed", "defects": checks_failed},
                actor_id=inspector_user.id
            )

        db.commit()
        return {
            "execution_id": execution.id,
            "verification_status": execution.verification_status,
            "is_success": is_success,
            "outcome_summary": execution.verification_outcome,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "incident_status": incident.status if incident else None
        }

recovery_verification_service = RecoveryVerificationService()
