from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _admin_headers():
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@campusops.edu", "password": "password123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_simulation_exam_room_unavailable():
    res = client.post("/api/v1/simulations/exam_room_unavailable", headers=_admin_headers())
    assert res.status_code == 200
    data = res.json()
    assert data["scenario"] == "examination_room_unavailable"
    assert "recovery_options" in data
    assert len(data["recovery_options"]) > 0

def test_simulation_technician_unavailable():
    res = client.post("/api/v1/simulations/technician_unavailable", headers=_admin_headers())
    assert res.status_code == 200
    data = res.json()
    assert data["scenario"] == "technician_unavailable"
    assert data["reassigned_successfully"] is True

def test_simulation_stock_shortage():
    res = client.post("/api/v1/simulations/stock_shortage", headers=_admin_headers())
    assert res.status_code == 200
    data = res.json()
    assert data["scenario"] == "critical_part_out_of_stock"
    assert data["work_order_blocked"] is True

def test_simulation_wifi_outage():
    res = client.post("/api/v1/simulations/wifi_outage", headers=_admin_headers())
    assert res.status_code == 200
    data = res.json()
    assert data["scenario"] == "multiple_wifi_complaints"
    assert data["canonical_incident"]["correlated_reports_count"] >= 4

def test_simulation_reset():
    res = client.post("/api/v1/simulations/reset", headers=_admin_headers())
    assert res.status_code == 200
    assert res.json()["status"] == "success"
