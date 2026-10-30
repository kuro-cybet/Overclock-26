import hashlib
import hmac
import json
import time

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def _token(email: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_inbound_email_requires_auth():
    response = client.post(
        "/api/v1/integrations/email/inbox",
        json={
            "sender_email": "student@campusops.edu",
            "subject": "No auth",
            "body": "Should be rejected.",
        },
    )
    assert response.status_code == 401


def test_inbound_email_rejects_non_admin():
    response = client.post(
        "/api/v1/integrations/email/inbox",
        json={
            "sender_email": "student@campusops.edu",
            "subject": "Student token",
            "body": "Should be forbidden.",
        },
        headers={"Authorization": f"Bearer {_token('student@campusops.edu')}"},
    )
    assert response.status_code == 403


def test_inbound_email_accepts_admin_token():
    response = client.post(
        "/api/v1/integrations/email/inbox",
        json={
            "sender_email": "prof.smith@campusops.edu",
            "subject": "Admin token",
            "body": "Should be accepted.",
        },
        headers={"Authorization": f"Bearer {_token('admin@campusops.edu')}"},
    )
    assert response.status_code == 200
    assert "outbox_id" in response.json()


def test_inbound_email_accepts_valid_signature(monkeypatch):
    monkeypatch.setattr(settings, "CAMPUSOPS_INBOUND_SECRET", "inbound-test-secret")

    body = json.dumps(
        {
            "sender_email": "prof.smith@campusops.edu",
            "subject": "Signed inbound",
            "body": "Should be accepted via HMAC.",
        },
        separators=(",", ":"),
    )
    timestamp = str(int(time.time()))
    signature = hmac.new(
        b"inbound-test-secret",
        f"{timestamp}.{body}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/api/v1/integrations/email/inbox",
        content=body,
        headers={
            "Content-Type": "application/json",
            "x-campusops-timestamp": timestamp,
            "x-campusops-signature": signature,
        },
    )
    assert response.status_code == 200


def test_inbound_email_rejects_bad_signature(monkeypatch):
    monkeypatch.setattr(settings, "CAMPUSOPS_INBOUND_SECRET", "inbound-test-secret")

    response = client.post(
        "/api/v1/integrations/email/inbox",
        content='{"sender_email":"student@campusops.edu","subject":"x","body":"y"}',
        headers={
            "Content-Type": "application/json",
            "x-campusops-timestamp": str(int(time.time())),
            "x-campusops-signature": "0" * 64,
        },
    )
    assert response.status_code == 401


def test_admin_endpoints_reject_anonymous_requests():
    assert client.post("/api/v1/notifications/outbox/process").status_code == 401
    assert client.post("/api/v1/simulations/reset").status_code == 401


def test_outbox_listing_requires_admin():
    anonymous = client.get("/api/v1/integrations/email/outbox")
    assert anonymous.status_code == 401

    student = client.get(
        "/api/v1/integrations/email/outbox",
        headers={"Authorization": f"Bearer {_token('student@campusops.edu')}"},
    )
    assert student.status_code == 403

    admin = client.get(
        "/api/v1/integrations/email/outbox",
        headers={"Authorization": f"Bearer {_token('admin@campusops.edu')}"},
    )
    assert admin.status_code == 200
