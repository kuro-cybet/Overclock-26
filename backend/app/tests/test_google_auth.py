"""Google sign-in contract.

The client only ever sends Google's ID token. The server decides the role from
the ``role_assignments`` allowlist, so an unassigned Google account can never
obtain a CampusOps token.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.database.connection import SessionLocal
from app.database.models.role_assignment import RoleAssignment
from app.main import app

client = TestClient(app)


def test_google_login_returns_503_when_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", None)

    response = client.post("/api/v1/auth/google", json={"credential": "anything"})
    assert response.status_code == 503, response.text


def test_google_login_rejects_invalid_credential(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")

    response = client.post("/api/v1/auth/google", json={"credential": "not-a-real-token"})
    assert response.status_code == 401, response.text


def test_password_login_is_disabled_by_default(monkeypatch):
    monkeypatch.setattr(settings, "PASSWORD_LOGIN_ENABLED", False)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@campusops.edu", "password": "password123"},
    )
    assert response.status_code == 403, response.text
    assert "Google" in response.json()["detail"]


def _fake_claims(monkeypatch, email: str, verified: bool = True):
    import google.oauth2.id_token as id_token

    def fake_verify(credential, request, audience):
        return {
            "email": email,
            "email_verified": verified,
            "sub": "google-sub-123",
            "name": "Test Person",
            "picture": "https://example.test/avatar.png",
        }

    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(id_token, "verify_oauth2_token", fake_verify)


def test_google_login_rejects_unassigned_account(monkeypatch):
    _fake_claims(monkeypatch, "nobody@example.com")

    response = client.post("/api/v1/auth/google", json={"credential": "fake"})
    assert response.status_code == 403, response.text


def test_google_login_grants_allowlisted_role(monkeypatch):
    email = "student@campusops.edu"
    db = SessionLocal()
    db.query(RoleAssignment).filter(RoleAssignment.email == email).delete()
    db.add(
        RoleAssignment(
            email=email,
            role="student",
            is_active=True,
            created_at=datetime.utcnow(),
        )
    )
    db.commit()
    db.close()

    try:
        _fake_claims(monkeypatch, email)
        response = client.post("/api/v1/auth/google", json={"credential": "fake"})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["user"]["email"] == email
        assert body["user"]["role"] == "student"
        assert body["access_token"]
    finally:
        db = SessionLocal()
        db.query(RoleAssignment).filter(RoleAssignment.email == email).delete()
        db.commit()
        db.close()
