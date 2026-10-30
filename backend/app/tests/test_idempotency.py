import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.state_machine import validate_transition
from app.core.exceptions import InvalidStateTransitionError

client = TestClient(app)

def test_state_machine_invalid_transition():
    # An already completed work order cannot go back to assigned
    with pytest.raises(InvalidStateTransitionError):
        validate_transition("work_order", "completed", "assigned")

def test_repeated_email_event_handling():
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@campusops.edu", "password": "password123"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Sending identical incoming email twice
    email_payload = {
        "sender_email": "prof.smith@campusops.edu",
        "subject": "Intermittent Wi-Fi signal in Computer Lab A",
        "body": "Signal drops repeatedly during presentations."
    }

    res1 = client.post("/api/v1/integrations/email/inbox", json=email_payload, headers=headers)
    assert res1.status_code == 200
    report_code_1 = res1.json()["report_code"]

    res2 = client.post("/api/v1/integrations/email/inbox", json=email_payload, headers=headers)
    assert res2.status_code == 200
    # Both handled safely without crashing, outbox generated
    assert "outbox_id" in res2.json()

