from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models.approval import ApprovalRequest, ProcurementRequest
from app.database.models.inventory import InventoryItem
from app.database.models.work_order import WorkOrder
from app.database.models.user import User
from app.core.exceptions import SeparationOfDutiesError, PermissionDeniedError, CampusOpsException

class ApprovalService:
    def decide_approval_request(
        self,
        db: Session,
        approval_id: str,
        approver_user: User,
        decision: str,  # approved or rejected
        decision_reason: str
    ) -> ApprovalRequest:
        req = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
        if not req:
            raise CampusOpsException("Approval request not found.", 404)

        if req.status != "pending":
            raise CampusOpsException(f"Approval request already decided with status: {req.status}", 400)

        # 1. Enforce Separation of Duties: Requester CANNOT approve their own submission!
        if req.requester_id == approver_user.id:
            raise SeparationOfDutiesError("Separation of duties violation: You cannot approve or decide your own submission.")

        # 2. Check role and authority:
        # System admin does NOT automatically get business approval authority!
        if approver_user.sub_role == "system_admin" and approver_user.sub_role not in ["procurement_approver", "department_manager"]:
            raise PermissionDeniedError(
                action="approve_business_request",
                reason="System Administrator role does not grant business approval authority. Department Manager or Procurement Approver required."
            )

        if req.approval_type == "purchase":
            if approver_user.sub_role != "procurement_approver" and approver_user.sub_role != "department_manager":
                raise PermissionDeniedError(action="approve_purchase", reason="Only Procurement Approver or Department Manager can approve purchases.")
        elif req.approval_type in ["costly_repair", "room_override"]:
            if approver_user.sub_role != "department_manager":
                raise PermissionDeniedError(action=req.approval_type, reason="Only Department Manager can authorize costly repairs and room overrides.")

        req.status = decision
        req.approver_id = approver_user.id
        req.decision_reason = decision_reason
        req.decided_at = datetime.utcnow()

        # Handle side-effects if approved
        if decision == "approved":
            if req.approval_type == "purchase" and req.target_entity_type == "procurement":
                proc = db.query(ProcurementRequest).filter(ProcurementRequest.id == req.target_entity_id).first()
                if proc:
                    proc.status = "ordered"
                    # simulate immediate receipt of ordered items into inventory
                    item = db.query(InventoryItem).filter(InventoryItem.id == proc.item_id).first()
                    if item:
                        item.stock_quantity += proc.quantity
                    proc.status = "received"
                    # If linked to a blocked work order, unblock it
                    if proc.work_order_id:
                        wo = db.query(WorkOrder).filter(WorkOrder.id == proc.work_order_id).first()
                        if wo and wo.status == "blocked":
                            wo.status = "in_progress"
                            wo.blocked_reason = None

        db.flush()
        return req

approval_service = ApprovalService()

