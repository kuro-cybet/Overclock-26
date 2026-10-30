import json
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database.models.staff import StaffProfile
from app.database.models.user import User
from app.database.models.work_order import WorkOrder
from app.services.assignment_service import assignment_service
from app.database.models.audit import AuditLog

class TechnicianAbsenceSimulation:
    def trigger(self, db: Session, technician_email: str = "tech@campusops.edu") -> Dict[str, Any]:
        tech_user = db.query(User).filter(User.email == technician_email).first()
        if not tech_user:
            tech_user = db.query(User).filter(User.role == "technician").first()

        profile = db.query(StaffProfile).filter(StaffProfile.user_id == tech_user.id).first()
        before_state = {
            "technician_id": tech_user.id,
            "name": tech_user.name,
            "email": tech_user.email,
            "availability": profile.availability_status if profile else "unknown",
            "workload": profile.current_workload if profile else 0
        }

        # Find active work orders assigned to this technician
        active_wo = db.query(WorkOrder).filter(
            WorkOrder.assigned_technician_id == tech_user.id,
            WorkOrder.status.in_(["assigned", "in_progress", "blocked"])
        ).first()

        # Mark technician absent and flush so queries see it
        if profile:
            profile.availability_status = "absent"
            db.flush()

        # Calculate eligible staff using skills, workload, shift
        req_skills = json.loads(active_wo.required_skills) if (active_wo and active_wo.required_skills) else ["network"]
        eligible = [cand for cand in assignment_service.find_eligible_technicians(db, req_skills) if cand["technician_id"] != tech_user.id]

        reassigned_to = None
        if active_wo and eligible:
            top_candidate = eligible[0]
            assignment_service.assign_technician_to_work_order(
                db=db,
                work_order_id=active_wo.id,
                technician_id=top_candidate["technician_id"],
                reassign_reason=f"Automated re-assignment due to absence of {tech_user.name}"
            )
            reassigned_to = top_candidate

        after_state = {
            "technician_id": tech_user.id,
            "name": tech_user.name,
            "email": tech_user.email,
            "availability": profile.availability_status if profile else "unknown",
            "reassigned_work_order": active_wo.work_order_code if active_wo else None,
            "new_assigned_technician": reassigned_to["name"] if reassigned_to else "Escalated to Supervisor"
        }

        # Audit
        audit = AuditLog(
            action="SIMULATION_TECHNICIAN_ABSENT",
            actor_id="admin-sim",
            actor_role="admin",
            entity_type="user",
            entity_id=tech_user.id,
            old_value=json.dumps(before_state),
            new_value=json.dumps(after_state),
            reason="Scenario Simulator: Technician marked absent with automated reassignment"
        )
        db.add(audit)
        db.flush()

        return {
            "scenario": "technician_unavailable",
            "summary": f"Technician {tech_user.name} marked absent. Eligible staff evaluated against skills, workload & shift.",
            "before_state": before_state,
            "after_state": after_state,
            "eligible_candidates_found": len(eligible),
            "reassigned_successfully": reassigned_to is not None
        }

technician_absence_sim = TechnicianAbsenceSimulation()
