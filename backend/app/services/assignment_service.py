import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.database.models.staff import StaffProfile
from app.database.models.user import User
from app.database.models.work_order import WorkOrder
from app.core.exceptions import CampusOpsException

class AssignmentService:
    def find_eligible_technicians(
        self,
        db: Session,
        required_skills: List[str],
        preferred_building_id: Optional[str] = None,
        preferred_shift: Optional[str] = "morning"
    ) -> List[Dict[str, Any]]:
        # Query active staff profiles who are available or on_task (not absent/on_leave)
        profiles = db.query(StaffProfile).filter(
            StaffProfile.availability_status.in_(["available", "on_task"])
        ).all()

        eligible = []
        for p in profiles:
            user = db.query(User).filter(User.id == p.user_id).first()
            if not user or not user.is_active:
                continue

            try:
                skills_list = json.loads(p.skills)
            except Exception:
                skills_list = []

            # Check if all or at least one required skill is present
            has_skills = any(s.lower() in [sk.lower() for sk in skills_list] for s in required_skills) if required_skills else True
            if not has_skills:
                continue

            # Calculate match score based on skills, building locality, shift, workload
            score = 100
            if preferred_building_id and p.assigned_building_id == preferred_building_id:
                score += 30
            if preferred_shift and p.shift == preferred_shift:
                score += 20
            # Penalize heavy current workload
            score -= (p.current_workload * 15)

            eligible.append({
                "technician_id": user.id,
                "name": user.name,
                "email": user.email,
                "sub_role": user.sub_role,
                "shift": p.shift,
                "building_id": p.assigned_building_id,
                "availability_status": p.availability_status,
                "current_workload": p.current_workload,
                "skills": skills_list,
                "suitability_score": score
            })

        eligible.sort(key=lambda x: x["suitability_score"], reverse=True)
        return eligible

    def assign_technician_to_work_order(
        self,
        db: Session,
        work_order_id: str,
        technician_id: Optional[str] = None,
        reassign_reason: Optional[str] = None
    ) -> WorkOrder:
        wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not wo:
            raise CampusOpsException(f"Work order '{work_order_id}' not found.", 404)

        req_skills = json.loads(wo.required_skills) if wo.required_skills else []

        selected_tech_id = technician_id
        if not selected_tech_id:
            eligible = self.find_eligible_technicians(db, req_skills)
            if not eligible:
                raise CampusOpsException("No qualified technician with matching skills and availability found for assignment.", 422)
            selected_tech_id = eligible[0]["technician_id"]

        # Validate that the selected technician has staff profile and is not absent
        staff_prof = db.query(StaffProfile).filter(StaffProfile.user_id == selected_tech_id).first()
        if not staff_prof or staff_prof.availability_status in ["absent", "on_leave"]:
            raise CampusOpsException("Cannot assign technician: technician is absent or on leave.", 409)

        # Update previous technician's workload if reassigning
        if wo.assigned_technician_id and wo.assigned_technician_id != selected_tech_id:
            old_prof = db.query(StaffProfile).filter(StaffProfile.user_id == wo.assigned_technician_id).first()
            if old_prof and old_prof.current_workload > 0:
                old_prof.current_workload -= 1

        wo.assigned_technician_id = selected_tech_id
        staff_prof.current_workload += 1
        wo.status = "assigned"
        if reassign_reason:
            wo.diagnosis = f"Reassigned: {reassign_reason}"

        db.flush()
        return wo

assignment_service = AssignmentService()

