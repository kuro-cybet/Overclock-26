from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.models.incident import Incident
from app.database.models.work_order import WorkOrder
from app.database.models.room import Room
from app.database.models.inventory import InventoryItem
from app.database.models.booking import RoomBooking
from app.database.models.staff import StaffProfile
from app.database.models.approval import ApprovalRequest

class AnalyticsService:
    def get_dashboard_analytics(self, db: Session) -> Dict[str, Any]:
        # 1. Open incidents count
        open_incidents = db.query(Incident).filter(
            Incident.status.in_(["open", "in_progress", "pending_parts", "pending_approval"])
        ).count()

        # 2. SLA compliance rate
        total_incidents = db.query(Incident).count()
        breached_incidents = db.query(Incident).filter(Incident.is_sla_breached == True).count()
        sla_rate = round(100.0 * (total_incidents - breached_incidents) / total_incidents, 1) if total_incidents > 0 else 100.0

        # 3. Active work orders
        active_work_orders = db.query(WorkOrder).filter(
            WorkOrder.status.in_(["assigned", "in_progress", "blocked", "pending_parts"])
        ).count()

        # 4. Room utilisation rate
        total_rooms = db.query(Room).count()
        occupied_or_booked = db.query(RoomBooking).filter(RoomBooking.status == "confirmed").count()
        room_utilisation = round(min(100.0, (occupied_or_booked / max(1, total_rooms)) * 40.0), 1)

        # 5. Parts shortages
        parts_shortages = db.query(InventoryItem).filter(
            (InventoryItem.stock_quantity - InventoryItem.reserved_quantity) <= InventoryItem.minimum_threshold
        ).count()

        # Category breakdown
        cat_counts = db.query(Incident.category, func.count(Incident.id)).group_by(Incident.category).all()
        incidents_by_category = {cat: count for cat, count in cat_counts}

        # Severity breakdown
        sev_counts = db.query(Incident.severity, func.count(Incident.id)).group_by(Incident.severity).all()
        incidents_by_severity = {sev: count for sev, count in sev_counts}

        # Work orders status breakdown
        wo_counts = db.query(WorkOrder.status, func.count(WorkOrder.id)).group_by(WorkOrder.status).all()
        work_orders_by_status = {st: count for st, count in wo_counts}

        # Room readiness breakdown
        readiness_counts = db.query(Room.daily_readiness_status, func.count(Room.id)).group_by(Room.daily_readiness_status).all()
        room_readiness_breakdown = {st: count for st, count in readiness_counts}

        # Pending approvals count
        pending_approvals = db.query(ApprovalRequest).filter(ApprovalRequest.status == "pending").count()

        # Synthetic monthly trend for chart
        monthly_trend = [
            {"month": "May", "resolved": 18, "breached": 2, "sla_rate": 90.0},
            {"month": "Jun", "resolved": 24, "breached": 3, "sla_rate": 88.9},
            {"month": "Jul", "resolved": 15, "breached": 1, "sla_rate": 93.8},
            {"month": "Aug", "resolved": 29, "breached": 2, "sla_rate": 93.5},
            {"month": "Sep", "resolved": 38, "breached": 4, "sla_rate": 90.5},
            {"month": "Oct", "resolved": 42, "breached": 3, "sla_rate": 93.3},
        ]

        return {
            "kpi": {
                "open_incidents": open_incidents,
                "sla_compliance_rate": sla_rate,
                "active_work_orders": active_work_orders,
                "room_utilisation_rate": room_utilisation,
                "parts_shortages": parts_shortages,
                "pending_approvals": pending_approvals
            },
            "incidents_by_category": incidents_by_category,
            "incidents_by_severity": incidents_by_severity,
            "work_orders_by_status": work_orders_by_status,
            "room_readiness_breakdown": room_readiness_breakdown,
            "sla_monthly_trend": monthly_trend
        }

analytics_service = AnalyticsService()

