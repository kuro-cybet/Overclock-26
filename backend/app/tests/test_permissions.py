import pytest
from app.core.permissions import has_permission, check_permission
from app.core.exceptions import PermissionDeniedError

def test_admin_permissions():
    assert has_permission("admin", "system_admin", "view:admin_dashboard") is True
    assert has_permission("admin", "system_admin", "run:simulations") is True
    assert has_permission("admin", "procurement_approver", "approve:procurement") is True
    # System admin does not automatically get procurement approval
    assert has_permission("admin", "system_admin", "approve:procurement") is False

def test_student_cannot_access_admin_action():
    assert has_permission("student", None, "view:admin_dashboard") is False
    with pytest.raises(PermissionDeniedError):
        check_permission("student", None, "view:admin_dashboard")

def test_technician_permissions():
    assert has_permission("technician", "maintenance_technician", "view:technician_dashboard") is True
    assert has_permission("technician", "maintenance_technician", "update:work_order_status") is True
    assert has_permission("technician", "janitor", "perform:cleaning") is True
    assert has_permission("technician", "all_skills_technician", "perform:repairs") is True
    assert has_permission("technician", "all_skills_technician", "perform:cleaning") is True
    assert has_permission("technician", "all_skills_technician", "inspect:room_equipment") is True
