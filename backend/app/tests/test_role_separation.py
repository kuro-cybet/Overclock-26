"""Role separation: portals are bound to users.role, with system_admin preview.

These tests cover the contract the frontend relies on:
  * every /api/v1 route requires a token (except login),
  * users can only open their own portal dashboard,
  * only system_admin can mint a preview token for another portal role,
  * admin-only data is not reachable from student/technician/faculty tokens.
"""

from fastapi.testclient import TestClient

from app.database.connection import SessionLocal
from app.database.models.notification import Notification
from app.database.models.user import User
from app.main import app

client = TestClient(app)


def _token(email: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _headers(email: str) -> dict:
    return {"Authorization": f"Bearer {_token(email)}"}


ADMIN_ENDPOINTS = [
    ("get", "/api/v1/users"),
    ("get", "/api/v1/analytics"),
    ("get", "/api/v1/staff"),
    ("get", "/api/v1/assets"),
    ("get", "/api/v1/sla/status"),
    ("get", "/api/v1/recovery/executions"),
]


def test_portal_data_requires_authentication():
    for method, path in ADMIN_ENDPOINTS:
        assert getattr(client, method)(path).status_code == 401, path

    assert client.get("/api/v1/work-orders").status_code == 401
    assert client.get("/api/v1/dashboard/admin").status_code == 401


def test_student_only_reaches_student_portal():
    headers = _headers("student@campusops.edu")

    assert client.get("/api/v1/dashboard/student", headers=headers).status_code == 200

    for portal in ("admin", "technician", "faculty"):
        response = client.get(f"/api/v1/dashboard/{portal}", headers=headers)
        assert response.status_code == 403, f"student opened /dashboard/{portal}"

    for method, path in ADMIN_ENDPOINTS:
        assert getattr(client, method)(path, headers=headers).status_code == 403, path

    assert client.get("/api/v1/work-orders", headers=headers).status_code == 403
    assert client.get("/api/v1/inventory", headers=headers).status_code == 403


def test_faculty_only_reaches_faculty_portal():
    headers = _headers("faculty@campusops.edu")

    assert client.get("/api/v1/dashboard/faculty", headers=headers).status_code == 200
    assert client.get("/api/v1/dashboard/admin", headers=headers).status_code == 403
    assert client.get("/api/v1/dashboard/technician", headers=headers).status_code == 403
    assert client.get("/api/v1/users", headers=headers).status_code == 403


def test_technician_sees_operations_but_not_admin_records():
    headers = _headers("tech@campusops.edu")

    assert client.get("/api/v1/dashboard/technician", headers=headers).status_code == 200
    assert client.get("/api/v1/dashboard/admin", headers=headers).status_code == 403
    assert client.get("/api/v1/work-orders", headers=headers).status_code == 200
    assert client.get("/api/v1/inventory", headers=headers).status_code == 200
    assert client.get("/api/v1/users", headers=headers).status_code == 403
    assert client.get("/api/v1/approvals", headers=headers).status_code == 403


def test_demo_accounts_endpoint_is_gone():
    headers = _headers("admin@campusops.edu")
    assert client.get("/api/v1/users/demo-accounts", headers=headers).status_code == 404


def test_only_system_admin_can_impersonate_a_portal():
    faculty = client.post(
        "/api/v1/auth/impersonate",
        json={"role": "student"},
        headers=_headers("faculty@campusops.edu"),
    )
    assert faculty.status_code == 403

    technician = client.post(
        "/api/v1/auth/impersonate",
        json={"role": "student"},
        headers=_headers("tech@campusops.edu"),
    )
    assert technician.status_code == 403


def test_system_admin_can_preview_each_portal_and_keeps_admin_token():
    admin_headers = _headers("admin@campusops.edu")

    for role in ("technician", "faculty", "student"):
        response = client.post(
            "/api/v1/auth/impersonate",
            json={"role": role},
            headers=admin_headers,
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["user"]["role"] == role
        assert body["impersonated_by"]

        preview_headers = {"Authorization": f"Bearer {body['access_token']}"}
        # Preview token behaves exactly like that role ...
        assert client.get(f"/api/v1/dashboard/{role}", headers=preview_headers).status_code == 200
        # ... and cannot reach another portal or admin records.
        assert client.get("/api/v1/dashboard/admin", headers=preview_headers).status_code == 403
        assert client.get("/api/v1/users", headers=preview_headers).status_code == 403

    # The original admin session is still intact.
    assert client.get("/api/v1/dashboard/admin", headers=admin_headers).status_code == 200
    assert client.get("/api/v1/users", headers=admin_headers).status_code == 200


def test_system_admin_cannot_impersonate_another_admin():
    response = client.post(
        "/api/v1/auth/impersonate",
        json={"role": "admin"},
        headers=_headers("admin@campusops.edu"),
    )
    assert response.status_code == 400


def test_notifications_cannot_be_marked_read_by_another_user():
    db = SessionLocal()
    try:
        student = db.query(User).filter(User.email == "student@campusops.edu").first()
        assert student is not None
        foreign = (
            db.query(Notification)
            .filter(
                Notification.recipient_id != student.id,
                Notification.recipient_role != "student",
            )
            .first()
        )
    finally:
        db.close()

    if not foreign:
        return  # seed data has no foreign notification in this environment

    response = client.patch(
        f"/api/v1/notifications/{foreign.id}/read",
        headers=_headers("student@campusops.edu"),
    )
    assert response.status_code == 403
