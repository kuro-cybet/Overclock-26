from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_incidents():
    res = client.get("/api/v1/incidents?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    assert "incident_code" in data[0]

def test_report_intake_with_ai_extraction():
    login_res = client.post("/api/v1/auth/login", json={
        "email": "student@campusops.edu",
        "password": "password123"
    })
    token = login_res.json()["access_token"]

    report_payload = {
        "title": "Broken projector in Computer Lab A",
        "description": "The projector lamp failed right before our class.",
        "category": "classroom",
        "urgency": "high"
    }

    res = client.post(
        "/api/v1/reports",
        json=report_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    report = res.json()
    assert report["category"] == "classroom"
    assert report["urgency"] == "high"
    assert "ai_extracted_meta" in report

