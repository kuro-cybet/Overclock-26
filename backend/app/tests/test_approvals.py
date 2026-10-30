from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_separation_of_duties_self_approval():
    # Login as facilities admin
    login_res = client.post("/api/v1/auth/login", json={
        "email": "facilities@campusops.edu",
        "password": "password123"
    })
    token = login_res.json()["access_token"]

    # Facilities admin requests an item
    inv_res = client.get("/api/v1/inventory?limit=1")
    item_id = inv_res.json()[0]["id"]

    proc_res = client.post("/api/v1/procurement", json={
        "item_id": item_id,
        "quantity": 2,
        "justification": "Self approval test"
    }, headers={"Authorization": f"Bearer {token}"})
    assert proc_res.status_code == 200
    approval_id = proc_res.json()["approval_request_id"]

    # Same requester tries to approve their own request -> MUST be rejected (403 Separation of Duties)
    decide_res = client.post(f"/api/v1/approvals/{approval_id}/decision", json={
        "decision": "approved",
        "decision_reason": "I approve my own request"
    }, headers={"Authorization": f"Bearer {token}"})
    assert decide_res.status_code == 403
    assert "Separation of duties" in decide_res.json()["detail"]

