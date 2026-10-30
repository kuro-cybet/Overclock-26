import json
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database.models.room import Room
from app.database.models.booking import RoomBooking
from app.database.models.work_order import WorkOrder
from app.database.models.staff import StaffProfile
from app.database.models.inventory import InventoryItem
from app.database.models.approval import ApprovalRequest, ProcurementRequest
from app.database.models.audit import AuditLog
from app.services.booking_service import booking_service
from app.services.assignment_service import assignment_service
from app.services.notification_service import notification_service
from app.core.exceptions import CampusOpsException

class RecoveryService:
    def generate_recovery_plan(
        self,
        db: Session,
        disruption_type: str,
        entity_id: str
    ) -> Dict[str, Any]:
        options = []
        current_impact = "Assessing disruption impact."

        if disruption_type == "exam_room_unavailable":
            # entity_id is room_id or booking_id
            booking = db.query(RoomBooking).filter(
                (RoomBooking.room_id == entity_id) | (RoomBooking.id == entity_id),
                RoomBooking.purpose == "examination",
                RoomBooking.status == "confirmed"
            ).first()

            if not booking:
                # Find any upcoming booking
                booking = db.query(RoomBooking).filter(
                    (RoomBooking.room_id == entity_id) | (RoomBooking.id == entity_id),
                    RoomBooking.status == "confirmed"
                ).first()

            orig_room = db.query(Room).filter(Room.id == (booking.room_id if booking else entity_id)).first()
            room_name = orig_room.name if orig_room else "Affected Room"
            current_impact = f"Exam session '{booking.title if booking else 'Scheduled Examination'}' in {room_name} is compromised due to facility disruption."

            required_features = json.loads(booking.equipment_required) if (booking and booking.equipment_required) else ["wifi"]
            cap = orig_room.capacity if orig_room else 50

            alternatives = booking_service.find_feasible_alternative_rooms(
                db=db,
                required_capacity=cap,
                required_features=required_features,
                start_time=booking.start_time if booking else datetime.utcnow(),
                end_time=booking.end_time if booking else datetime.utcnow(),
                exclude_room_id=orig_room.id if orig_room else None
            )

            for idx, alt in enumerate(alternatives[:3]):
                options.append({
                    "option_id": f"relocate_to_{alt['room_id']}",
                    "title": f"Relocate to {alt['name']} ({alt['room_number']})",
                    "description": f"Move exam to {alt['name']}. Capacity: {alt['capacity']} seats. All dependencies satisfied.",
                    "impact_assessment": "Zero exam cancellation; preserves student start time.",
                    "feasibility_score": round(alt["feasibility_score"] / 100.0, 2),
                    "requires_approval": True,
                    "approval_role": "department_manager",
                    "target_action": "relocate_booking",
                    "action_payload": {
                        "booking_id": booking.id if booking else "",
                        "original_room_id": orig_room.id if orig_room else "",
                        "new_room_id": alt["room_id"],
                        "new_room_name": alt["name"]
                    }
                })

        elif disruption_type == "technician_absent":
            # entity_id is technician user_id or work_order_id
            wo = db.query(WorkOrder).filter(
                (WorkOrder.assigned_technician_id == entity_id) | (WorkOrder.id == entity_id),
                WorkOrder.status.in_(["assigned", "in_progress", "blocked"])
            ).first()

            skills = json.loads(wo.required_skills) if (wo and wo.required_skills) else ["network"]
            current_impact = f"Work Order {wo.work_order_code if wo else 'N/A'} blocked because assigned technician is unavailable."

            eligible = assignment_service.find_eligible_technicians(db, skills)
            for idx, cand in enumerate(eligible[:3]):
                options.append({
                    "option_id": f"reassign_to_{cand['technician_id']}",
                    "title": f"Reassign to {cand['name']} ({cand['sub_role'].replace('_', ' ').capitalize()})",
                    "description": f"Shift: {cand['shift'].capitalize()}. Current workload: {cand['current_workload']} tasks. Matching skills: {cand['skills']}.",
                    "impact_assessment": "Maintains SLA deadline; zero work order cancellation.",
                    "feasibility_score": round(cand["suitability_score"] / 120.0, 2),
                    "requires_approval": False,
                    "approval_role": None,
                    "target_action": "reassign_work_order",
                    "action_payload": {
                        "work_order_id": wo.id if wo else "",
                        "new_technician_id": cand["technician_id"],
                        "new_technician_name": cand["name"]
                    }
                })

        elif disruption_type == "stock_shortage":
            item = db.query(InventoryItem).filter(InventoryItem.id == entity_id).first()
            current_impact = f"Component '{item.name if item else 'Critical Hardware'}' has 0 available units, blocking active work orders."

            options.append({
                "option_id": "procure_emergency_stock",
                "title": "Emergency Procurement Expedited Order",
                "description": f"Create urgent procurement purchase order for 5x units with immediate automated dispatch.",
                "impact_assessment": "Resolves parts block within 2 hours once authorized.",
                "feasibility_score": 0.95,
                "requires_approval": True,
                "approval_role": "procurement_approver",
                "target_action": "create_procurement_request",
                "action_payload": {
                    "item_id": item.id if item else entity_id,
                    "quantity": 5,
                    "estimated_cost": (item.unit_cost if item else 200.0) * 5
                }
            })

        return {
            "disruption_type": disruption_type,
            "entity_id": entity_id,
            "current_impact": current_impact,
            "options": options
        }

    def execute_recovery_plan(
        self,
        db: Session,
        target_action: str,
        action_payload: Dict[str, Any],
        actor_id: str,
        actor_role: str,
        approval_override: bool = False
    ) -> Dict[str, Any]:
        # Page 8: "Recovery: Revalidate permissions, room availability, staff availability, stock and approvals immediately before execution."
        now = datetime.utcnow()

        if target_action == "relocate_booking":
            booking_id = action_payload.get("booking_id")
            new_room_id = action_payload.get("new_room_id")
            booking = db.query(RoomBooking).filter(RoomBooking.id == booking_id).first()
            if not booking:
                raise CampusOpsException("Booking not found.", 404)

            # Revalidate availability of new room right before execution
            is_avail = booking_service.check_room_availability(db, new_room_id, booking.start_time, booking.end_time)
            if not is_avail:
                raise CampusOpsException("Revalidation failed: The proposed destination room is no longer available.", 409)

            orig_room_id = booking.room_id
            booking.room_id = new_room_id
            booking.conflict_resolved_to_room_id = new_room_id
            booking.status = "relocated"

            # Targeted notifications to faculty & students
            new_room = db.query(Room).filter(Room.id == new_room_id).first()
            notification_service.create_in_app_notification(
                db=db,
                recipient_id=booking.user_id,
                recipient_role="faculty",
                title="Exam Relocation Confirmed",
                message=f"Exam '{booking.title}' has been successfully relocated to {new_room.name} ({new_room.room_number}).",
                notif_type="action_required",
                link_url="/faculty/timetable"
            )
            notification_service.broadcast_role_notification(
                db=db,
                role="student",
                title="Exam Room Change Alert",
                message=f"Notice: {booking.title} has moved to {new_room.name} ({new_room.room_number}). Please report there.",
                notif_type="warning",
                link_url="/student/dashboard"
            )

            # Audit
            audit = AuditLog(
                action="RECOVERY_EXAM_RELOCATED",
                actor_id=actor_id,
                actor_role=actor_role,
                entity_type="room_booking",
                entity_id=booking.id,
                new_value=json.dumps({"original_room": orig_room_id, "new_room": new_room_id}),
                reason="Automatic recovery execution: Exam room relocated due to facility disruption."
            )
            db.add(audit)
            db.flush()
            return {"status": "success", "message": f"Exam relocated to {new_room.name}.", "booking_id": booking.id}

        elif target_action == "reassign_work_order":
            wo_id = action_payload.get("work_order_id")
            new_tech_id = action_payload.get("new_technician_id")
            
            # Revalidate technician availability
            prof = db.query(StaffProfile).filter(StaffProfile.user_id == new_tech_id).first()
            if not prof or prof.availability_status in ["absent", "on_leave"]:
                raise CampusOpsException("Revalidation failed: Replacement technician is no longer available.", 409)

            wo = assignment_service.assign_technician_to_work_order(
                db=db,
                work_order_id=wo_id,
                technician_id=new_tech_id,
                reassign_reason="Recovery engine re-dispatch"
            )

            # Notification to new technician
            notification_service.create_in_app_notification(
                db=db,
                recipient_id=new_tech_id,
                recipient_role="technician",
                title="Priority Work Order Reassignment",
                message=f"Work Order {wo.work_order_code} has been reassigned to you under automated recovery.",
                notif_type="action_required",
                link_url=f"/technician/tasks"
            )

            # Audit
            audit = AuditLog(
                action="RECOVERY_WORK_ORDER_REASSIGNED",
                actor_id=actor_id,
                actor_role=actor_role,
                entity_type="work_order",
                entity_id=wo.id,
                new_value=json.dumps({"new_technician_id": new_tech_id}),
                reason="Recovery engine reassignment due to technician unavailability."
            )
            db.add(audit)
            db.flush()
            return {"status": "success", "message": f"Work order reassigned successfully.", "work_order_id": wo.id}

        elif target_action == "create_procurement_request":
            item_id = action_payload.get("item_id")
            qty = action_payload.get("quantity", 5)
            cost = action_payload.get("estimated_cost", 500.0)

            proc = ProcurementRequest(
                request_code=f"PRQ-{datetime.utcnow().strftime('%Y%m')}-REC",
                item_id=item_id,
                quantity=qty,
                estimated_cost=cost,
                requester_id=actor_id,
                status="approved" if approval_override else "requested"
            )
            db.add(proc)
            db.flush()

            # Create approval request if not overridden
            if not approval_override:
                app = ApprovalRequest(
                    approval_type="purchase",
                    target_entity_type="procurement",
                    target_entity_id=proc.id,
                    requester_id=actor_id,
                    status="pending",
                    cost_amount=cost,
                    justification="Emergency stock replenishment initiated via Disruption Recovery Engine."
                )
                db.add(app)

            return {"status": "success", "message": "Procurement request initiated.", "procurement_id": proc.id}

        raise CampusOpsException(f"Unknown recovery action '{target_action}'.", 400)

recovery_service = RecoveryService()

