from typing import List, Optional
from app.core.exceptions import PermissionDeniedError

ROLE_HIERARCHY = {
    "admin": ["admin"],
    "technician": ["technician"],
    "faculty": ["faculty"],
    "student": ["student"],
}

# ──────────────────────────────────────────────────────────────────────────────
# Base role permissions
# NOTE: The generic "admin" base-role only gets a minimal shared set.
#       Full admin power is gated behind the "system_admin" sub-role.
#       Every other admin sub-role gets only its domain scope.
# ──────────────────────────────────────────────────────────────────────────────
ROLE_PERMISSIONS = {
    # Shared admin base — intentionally narrow; sub-roles add domain access
    "admin": [
        "view:admin_dashboard",
    ],
    "technician": [
        "view:technician_dashboard",
        "view:assigned_work_orders",
        "update:work_order_status",
        "request:inventory_parts",
        "perform:room_readiness",
        "view:readiness_history",
    ],
    "faculty": [
        "view:faculty_dashboard",
        "view:timetable",
        "create:room_booking",
        "create:faculty_report",
        "view:own_reports",
        "confirm:exam_relocation",
    ],
    "student": [
        "view:student_dashboard",
        "create:student_report",
        "view:own_reports",
        "view:public_facilities",
        "submit:feedback",
    ],
}

# ──────────────────────────────────────────────────────────────────────────────
# Sub-role permissions — each admin sub-role is additive on top of base "admin"
# system_admin is a superset of ALL admin permissions (full control)
# ──────────────────────────────────────────────────────────────────────────────

# The complete set of admin operational permissions for system_admin
# (Note: Separation of duties means approve:procurement belongs exclusively to procurement_approver)
_SYSTEM_ADMIN_PERMISSIONS = [
    "view:admin_dashboard",
    "view:all_incidents",
    "manage:incidents",
    "manage:work_orders",
    "view:analytics",
    "run:simulations",
    "view:audit_logs",
    "manage:campus_assets",
    "manage:rooms",
    "view:all_reports",
    "trigger:recovery",
    "manage:staff",
    "manage:inventory",
    "manage:room_readiness",
    "override:room_status",
    "coordinate:facilities",
    "view:inventory_costs",
    "manage:users",
    "manage:system_config",
    "view:system_logs",
]

SUB_ROLE_PERMISSIONS: dict[str, list[str]] = {
    # ── System Administrator: FULL technical & operational control ─────────────
    "system_admin": _SYSTEM_ADMIN_PERMISSIONS,

    # ── Department Manager: incidents, approvals, department analytics ─────────
    "department_manager": [
        "view:admin_dashboard",
        "view:all_incidents",
        "manage:incidents",
        "approve:department_requests",
        "approve:overrides",
        "view:department_analytics",
        "view:analytics",
        "view:all_reports",
    ],

    # ── Facilities Administrator: rooms, assets, campus readiness, work orders ─
    "facilities_admin": [
        "view:admin_dashboard",
        "manage:campus_assets",
        "manage:rooms",
        "manage:room_readiness",
        "override:room_status",
        "coordinate:facilities",
        "manage:work_orders",
        "view:all_incidents",
        "view:all_reports",
    ],

    # ── Procurement Approver: inventory and purchase approvals only ────────────
    "procurement_approver": [
        "view:admin_dashboard",
        "approve:procurement",
        "view:inventory_costs",
        "manage:inventory",
        "view:all_reports",
    ],

    # ── Technician sub-roles ───────────────────────────────────────────────────
    "floor_incharge": ["coordinate:floor_tasks", "signoff:floor_readiness"],
    "maintenance_technician": ["perform:repairs", "consume:parts"],
    "janitor": ["perform:cleaning", "report:sanitation"],
    "room_incharge": ["signoff:room_readiness", "inspect:room_equipment"],
}

# ──────────────────────────────────────────────────────────────────────────────
# Pages each admin sub-role is allowed to navigate to (used by the frontend)
# ──────────────────────────────────────────────────────────────────────────────
ADMIN_SUB_ROLE_PAGES: dict[str, list[str]] = {
    "system_admin": [
        "dashboard", "incidents", "campus", "work-orders",
        "inventory", "approvals", "staff", "simulator", "analytics",
    ],
    "department_manager": [
        "dashboard", "incidents", "approvals", "analytics",
    ],
    "facilities_admin": [
        "dashboard", "campus", "incidents", "work-orders",
    ],
    "procurement_approver": [
        "dashboard", "inventory", "approvals",
    ],
}


def has_permission(user_role: str, user_sub_role: Optional[str], required_permission: str) -> bool:
    base_perms = ROLE_PERMISSIONS.get(user_role, [])
    if required_permission in base_perms:
        return True

    if user_sub_role:
        sub_perms = SUB_ROLE_PERMISSIONS.get(user_sub_role, [])
        if required_permission in sub_perms:
            return True

    return False


def check_permission(user_role: str, user_sub_role: Optional[str], required_permission: str):
    if not has_permission(user_role, user_sub_role, required_permission):
        raise PermissionDeniedError(
            action=required_permission,
            reason=f"Role '{user_role}' (sub-role: '{user_sub_role}') lacks permission '{required_permission}'",
        )

