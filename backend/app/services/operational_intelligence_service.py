from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from app.database.models.incident import Incident
from app.database.models.room import Room
from app.database.models.campus import Building, Floor
from app.database.models.asset import Asset
from app.database.models.booking import RoomBooking
from app.database.models.staff import StaffProfile
from app.database.models.user import User
from app.database.models.inventory import InventoryItem
from app.database.models.work_order import WorkOrder
from app.database.models.impact import IncidentImpactRecord
from app.database.models.explanation import DecisionExplanation
from app.database.models.maintenance import AssetMaintenanceHistory

class OperationalIntelligenceService:
    """
    Central Operational Intelligence Engine for CampusOps.
    Synthesizes signals across incidents, spatial assets, staff workloads,
    inventory stock, exam timetables, and SLA deadlines.
    """

    def get_full_operational_assessment(self, db: Session) -> Dict[str, Any]:
        """
        Executes a holistic multi-dimensional risk synthesis across the university.
        """
        now = datetime.utcnow()
        building_clusters = self.detect_building_incident_clusters(db)
        rooms_at_risk = self.detect_rooms_at_risk(db)
        exam_threats = self.detect_affected_examinations(db)
        overloaded_techs = self.detect_overloaded_technicians(db)
        stock_shortages = self.detect_critical_inventory_shortages(db)
        sla_risks = self.detect_sla_breach_projections(db)
        repeated_failures = self.detect_repeated_asset_failures(db)

        # Calculate systemic operational readiness score (0 - 100)
        penalty = (
            len(building_clusters) * 8 +
            len(rooms_at_risk) * 5 +
            len(exam_threats) * 15 +
            len(overloaded_techs) * 6 +
            len(stock_shortages) * 7 +
            len(sla_risks) * 10 +
            len(repeated_failures) * 4
        )
        systemic_readiness_score = max(10, min(100, 100 - penalty))

        return {
            "timestamp": now.isoformat(),
            "systemic_readiness_score": systemic_readiness_score,
            "systemic_status": "nominal" if systemic_readiness_score >= 80 else ("degraded" if systemic_readiness_score >= 50 else "critical"),
            "summary_metrics": {
                "active_incident_clusters": len(building_clusters),
                "rooms_at_risk": len(rooms_at_risk),
                "exams_at_risk": len(exam_threats),
                "overloaded_technicians": len(overloaded_techs),
                "critical_stock_shortages": len(stock_shortages),
                "sla_at_risk_incidents": len(sla_risks),
                "chronic_failing_assets": len(repeated_failures),
            },
            "findings": {
                "building_clusters": building_clusters,
                "rooms_at_risk": rooms_at_risk,
                "affected_examinations": exam_threats,
                "overloaded_technicians": overloaded_techs,
                "inventory_shortages": stock_shortages,
                "sla_projections": sla_risks,
                "repeated_asset_failures": repeated_failures,
            }
        }

    def detect_building_incident_clusters(self, db: Session) -> List[Dict[str, Any]]:
        """
        Identifies buildings with multiple concurrent incidents, signaling possible
        systemic failures (e.g., electrical outage or network backbone failure).
        """
        # Active incident statuses
        active_statuses = ["open", "in_progress", "pending_parts", "pending_approval"]
        
        # Query active incidents joined with rooms and buildings
        results = (
            db.query(
                Building.id,
                Building.name,
                Building.code,
                func.count(Incident.id).label("incident_count")
            )
            .join(Room, Room.building_id == Building.id)
            .join(Incident, Incident.room_id == Room.id)
            .filter(Incident.status.in_(active_statuses))
            .group_by(Building.id, Building.name, Building.code)
            .having(func.count(Incident.id) >= 2)
            .all()
        )

        clusters = []
        for b_id, b_name, b_code, count in results:
            # Fetch detailed active incidents in this building
            incidents = (
                db.query(Incident)
                .join(Room, Incident.room_id == Room.id)
                .filter(Room.building_id == b_id, Incident.status.in_(active_statuses))
                .all()
            )

            categories = list({inc.category for inc in incidents})
            max_priority = "P4"
            for inc in incidents:
                if inc.priority == "P1":
                    max_priority = "P1"
                    break
                elif inc.priority == "P2" and max_priority in ["P3", "P4"]:
                    max_priority = "P2"
                elif inc.priority == "P3" and max_priority == "P4":
                    max_priority = "P3"

            clusters.append({
                "building_id": b_id,
                "building_name": b_name,
                "building_code": b_code,
                "active_incident_count": count,
                "categories": categories,
                "highest_priority": max_priority,
                "severity": "critical" if count >= 4 or max_priority == "P1" else "high",
                "recommended_action": (
                    f"Deploy multi-disciplinary response team to {b_name} ({b_code}). "
                    f"Possible common-mode failure across {', '.join(categories)}."
                ),
                "incident_codes": [inc.incident_code for inc in incidents[:5]]
            })

        return sorted(clusters, key=lambda x: x["active_incident_count"], reverse=True)

    def detect_rooms_at_risk(self, db: Session) -> List[Dict[str, Any]]:
        """
        Identifies rooms that have unresolved maintenance, physical damage,
        or open work orders, especially those with immediate bookings scheduled.
        """
        active_statuses = ["open", "in_progress", "pending_parts", "pending_approval"]
        now = datetime.utcnow()
        window_end = now + timedelta(hours=8)

        # Rooms with non-operational status or open incidents
        rooms = (
            db.query(Room)
            .outerjoin(Incident, and_(Incident.room_id == Room.id, Incident.status.in_(active_statuses)))
            .filter(or_(Room.status.in_(["under_maintenance", "unavailable"]), Incident.id.isnot(None)))
            .distinct()
            .all()
        )

        rooms_at_risk = []
        for r in rooms:
            building = db.query(Building).filter(Building.id == r.building_id).first()
            
            # Check upcoming bookings for this room in next 8 hours
            bookings = (
                db.query(RoomBooking)
                .filter(
                    RoomBooking.room_id == r.id,
                    RoomBooking.end_time >= now,
                    RoomBooking.start_time <= window_end,
                    RoomBooking.status != "cancelled"
                )
                .all()
            )

            # Check open work orders
            wos = (
                db.query(WorkOrder)
                .join(Incident, WorkOrder.incident_id == Incident.id)
                .filter(Incident.room_id == r.id, WorkOrder.status.in_(["assigned", "in_progress", "blocked"]))
                .all()
            )

            has_blocked_wo = any(wo.status == "blocked" for wo in wos)
            has_exam = any((b.purpose or "").lower() == "examination" for b in bookings)

            risk_level = "critical" if (has_exam or has_blocked_wo) else ("high" if bookings else "medium")

            rooms_at_risk.append({
                "room_id": r.id,
                "room_code": r.room_number,
                "room_name": r.name,
                "building_name": building.name if building else "Main Campus",
                "maintenance_status": r.status,
                "open_work_orders_count": len(wos),
                "has_blocked_parts": has_blocked_wo,
                "upcoming_bookings_count": len(bookings),
                "has_scheduled_exam": has_exam,
                "risk_level": risk_level,
                "recommended_action": (
                    f"Immediate room inspection or emergency relocation required for {r.room_number}. "
                    + ("Exam scheduled within 8 hours!" if has_exam else "Class schedule at risk.")
                )
            })

        return sorted(rooms_at_risk, key=lambda x: (x["risk_level"] == "critical", x["upcoming_bookings_count"]), reverse=True)

    def detect_affected_examinations(self, db: Session) -> List[Dict[str, Any]]:
        """
        Pinpoints examinations jeopardized by room faults, HVAC downtime, or electrical issues.
        """
        active_statuses = ["open", "in_progress", "pending_parts", "pending_approval"]
        now = datetime.utcnow()
        lookahead = now + timedelta(days=2)

        exam_bookings = (
            db.query(RoomBooking)
            .filter(
                RoomBooking.purpose == "examination",
                RoomBooking.end_time >= now,
                RoomBooking.start_time <= lookahead,
                RoomBooking.status != "cancelled"
            )
            .all()
        )

        threatened_exams = []
        for b in exam_bookings:
            room = db.query(Room).filter(Room.id == b.room_id).first()
            if not room:
                continue

            # Check room maintenance status or open incidents
            open_incident = (
                db.query(Incident)
                .filter(Incident.room_id == room.id, Incident.status.in_(active_statuses))
                .first()
            )

            if room.status != "available" or open_incident:
                building = db.query(Building).filter(Building.id == room.building_id).first()
                time_until_start = (b.start_time - now).total_seconds() / 3600.0

                threatened_exams.append({
                    "booking_id": b.id,
                    "exam_title": b.title,
                    "room_id": room.id,
                    "room_code": room.room_number,
                    "building_name": building.name if building else "Main Campus",
                    "start_time": b.start_time.isoformat(),
                    "hours_until_exam": round(max(0.0, time_until_start), 1),
                    "room_condition": room.status,
                    "incident_title": open_incident.title if open_incident else "Facility maintenance flag",
                    "severity": "critical" if time_until_start <= 4.0 else "high",
                    "recommended_action": f"Trigger Room Relocation Protocol for exam '{b.title}' from {room.room_number}."
                })

        return sorted(threatened_exams, key=lambda x: x["hours_until_exam"])

    def detect_overloaded_technicians(self, db: Session) -> List[Dict[str, Any]]:
        """
        Monitors staff workloads to prevent burn-out, dispatch bottlenecks, and SLA failures.
        """
        # Active work orders per technician
        tech_profiles = db.query(StaffProfile).all()
        overloaded = []

        for p in tech_profiles:
            user = db.query(User).filter(User.id == p.user_id).first()
            if not user:
                continue

            active_wos = (
                db.query(WorkOrder)
                .filter(
                    WorkOrder.assigned_technician_id == user.id,
                    WorkOrder.status.in_(["assigned", "in_progress", "blocked"])
                )
                .all()
            )

            p1_p2_count = sum(1 for wo in active_wos if wo.priority in ["P1", "P2"])
            load_count = len(active_wos)

            # Overloaded if >= 4 active work orders or >= 2 high-priority orders
            if load_count >= 3 or p1_p2_count >= 2:
                overloaded.append({
                    "technician_id": user.id,
                    "technician_name": user.name,
                    "email": user.email,
                    "shift_status": p.shift or "morning",
                    "active_work_orders": load_count,
                    "high_priority_orders": p1_p2_count,
                    "skills": p.skills or "General",
                    "load_factor": round(min(1.0, load_count / 5.0), 2),
                    "status": "critical_overload" if load_count >= 4 else "elevated_workload",
                    "recommended_action": f"Rebalance queue: divert new intake dispatches away from {user.name}."
                })

        return sorted(overloaded, key=lambda x: x["active_work_orders"], reverse=True)

    def detect_critical_inventory_shortages(self, db: Session) -> List[Dict[str, Any]]:
        """
        Surfaces spare parts and materials that have fallen below replenishment safety stocks.
        """
        items = db.query(InventoryItem).filter(
            or_(
                InventoryItem.stock_quantity <= InventoryItem.minimum_threshold,
                InventoryItem.stock_quantity == 0
            )
        ).all()

        shortages = []
        for it in items:
            # Check how many work orders are blocked specifically on parts for this category
            blocked_wos = (
                db.query(WorkOrder)
                .filter(WorkOrder.status == "blocked", WorkOrder.blocked_reason.ilike(f"%{it.name}%"))
                .count()
            )

            shortages.append({
                "item_id": it.id,
                "item_code": it.item_code,
                "name": it.name,
                "category": it.category,
                "stock_quantity": it.stock_quantity,
                "reserved_quantity": it.reserved_quantity,
                "available_quantity": max(0, it.stock_quantity - it.reserved_quantity),
                "minimum_threshold": it.minimum_threshold,
                "unit_cost": float(it.unit_cost or 0.0),
                "is_out_of_stock": it.stock_quantity <= 0,
                "blocked_work_orders": blocked_wos,
                "recommended_action": (
                    f"Immediate purchase order required for {it.name} (SKU: {it.item_code}). "
                    f"Stock: {it.stock_quantity} (Min: {it.minimum_threshold})."
                )
            })

        return sorted(shortages, key=lambda x: (x["is_out_of_stock"], x["blocked_work_orders"]), reverse=True)

    def detect_sla_breach_projections(self, db: Session) -> List[Dict[str, Any]]:
        """
        Calculates incidents approaching SLA deadlines within 45 minutes or already breached.
        """
        active_statuses = ["open", "in_progress", "pending_parts", "pending_approval"]
        now = datetime.utcnow()
        threshold = now + timedelta(minutes=45)

        incidents = (
            db.query(Incident)
            .filter(
                Incident.status.in_(active_statuses),
                Incident.sla_due_at.isnot(None),
                Incident.sla_due_at <= threshold
            )
            .all()
        )

        risks = []
        for inc in incidents:
            minutes_remaining = (inc.sla_due_at - now).total_seconds() / 60.0
            is_already_breached = minutes_remaining <= 0 or inc.is_sla_breached

            # Find assigned technician
            wo = db.query(WorkOrder).filter(WorkOrder.incident_id == inc.id).first()
            tech_name = "Unassigned"
            if wo and wo.assigned_technician_id:
                tech = db.query(User).filter(User.id == wo.assigned_technician_id).first()
                if tech:
                    tech_name = tech.name

            risks.append({
                "incident_id": inc.id,
                "incident_code": inc.incident_code,
                "title": inc.title,
                "priority": inc.priority,
                "status": inc.status,
                "sla_target_at": inc.sla_due_at.isoformat() if inc.sla_due_at else None,
                "minutes_remaining": round(minutes_remaining, 1),
                "is_breached": is_already_breached,
                "assigned_technician": tech_name,
                "urgency_level": "breached" if is_already_breached else ("critical" if minutes_remaining <= 15 else "warning"),
                "recommended_action": (
                    f"Escalate {inc.incident_code} to supervisory queue immediately. "
                    + ("SLA BREACHED!" if is_already_breached else f"{int(minutes_remaining)} minutes remaining.")
                )
            })

        return sorted(risks, key=lambda x: x["minutes_remaining"])

    def detect_repeated_asset_failures(self, db: Session) -> List[Dict[str, Any]]:
        """
        Identifies lemon / chronic failure assets that repeatedly breakdown.
        """
        assets = db.query(Asset).all()

        chronic = []
        for a in assets:
            failure_count = db.query(Incident).filter(Incident.asset_id == a.id).count()
            maint_count = db.query(AssetMaintenanceHistory).filter(AssetMaintenanceHistory.asset_id == a.id).count()

            if failure_count >= 2 or a.status in ["degraded", "inoperable"]:
                room = db.query(Room).filter(Room.id == a.room_id).first()
                building = db.query(Building).filter(Building.id == room.building_id).first() if room else None

                chronic.append({
                    "asset_id": a.id,
                    "asset_tag": a.asset_tag,
                    "name": a.name,
                    "category": a.category,
                    "location": f"{building.name if building else 'Campus'} - {room.room_number if room else 'Unknown'}",
                    "health_score": 45 if failure_count >= 3 else 60,
                    "failure_count": failure_count,
                    "maintenance_records_count": maint_count,
                    "condition_status": a.status or "operational",
                    "recommended_action": (
                        f"Flag {a.asset_tag} ({a.name}) for complete overhaul or capital replacement. "
                        f"Recurrent breakdowns ({failure_count} logged failures)."
                    )
                })

        return sorted(chronic, key=lambda x: (x["failure_count"], -x["health_score"]), reverse=True)

operational_intelligence_service = OperationalIntelligenceService()
