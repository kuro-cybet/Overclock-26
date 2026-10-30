from app.database.models.user import User
from app.database.models.campus import Building, Floor
from app.database.models.room import Room
from app.database.models.asset import Asset
from app.database.models.staff import StaffProfile
from app.database.models.report import Report
from app.database.models.incident import Incident
from app.database.models.work_order import WorkOrder
from app.database.models.booking import RoomBooking
from app.database.models.inventory import InventoryItem, StockReservation
from app.database.models.approval import ApprovalRequest, ProcurementRequest
from app.database.models.notification import Notification, NotificationOutbox
from app.database.models.audit import AuditLog
from app.database.models.intelligence import HistoricalResolution, PredictiveAlert

# V2 Models matching existing database schema
from app.database.models.technician_skill import Skill, TechnicianSkill, WorkOrderSkillRequirement
from app.database.models.work_order_checklist import WorkOrderChecklistItem
from app.database.models.inventory_transaction import InventoryTransaction
from app.database.models.approval_history import ApprovalHistory
from app.database.models.operational_event import OperationalEvent
from app.database.models.recovery import RecoveryExecution, RecoveryAction
from app.database.models.maintenance import AssetMaintenanceHistory, PreventiveMaintenanceSchedule
from app.database.models.impact import IncidentImpactRecord
from app.database.models.explanation import DecisionExplanation

__all__ = [
    "User",
    "Building",
    "Floor",
    "Room",
    "Asset",
    "StaffProfile",
    "Report",
    "Incident",
    "WorkOrder",
    "RoomBooking",
    "InventoryItem",
    "StockReservation",
    "ApprovalRequest",
    "ProcurementRequest",
    "Notification",
    "NotificationOutbox",
    "AuditLog",
    "HistoricalResolution",
    "PredictiveAlert",
    # V2
    "Skill",
    "TechnicianSkill",
    "WorkOrderSkillRequirement",
    "WorkOrderChecklistItem",
    "InventoryTransaction",
    "ApprovalHistory",
    "OperationalEvent",
    "RecoveryExecution",
    "RecoveryAction",
    "AssetMaintenanceHistory",
    "PreventiveMaintenanceSchedule",
    "IncidentImpactRecord",
    "DecisionExplanation",
]
