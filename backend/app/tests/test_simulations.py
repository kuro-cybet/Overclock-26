from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_simulation_exam_room_unavailable():
    res = client.post("/api/v1/simulations/exam_room_unavailable")
    assert res.status_code == 200
    data = res.json()
    assert data["scenario"] == "examination_room_unavailable"
    assert "recovery_options" in data
    assert len(data["recovery_options"]) > 0

def test_simulation_technician_unavailable():
    res = client.post("/api/v1/simulations/technician_unavailable")
    assert res.status_code == 200
    data = res.json()
    assert data["scenario"] == "technician_unavailable"
    assert data["reassigned_successfully"] is True

def test_simulation_stock_shortage():
    res = client.post("/api/v1/simulations/stock_shortage")
    assert res.status_code == 200
    data = res.json()
    assert data["scenario"] == "critical_part_out_of_stock"
    assert data["work_order_blocked"] is True

def test_simulation_wifi_outage():
    res = client.post("/api/v1/simulations/wifi_outage")
    assert res.status_code == 200
    data = res.json()
    assert data["scenario"] == "multiple_wifi_complaints"
    assert data["canonical_incident"]["correlated_reports_count"] >= 4

def test_simulation_reset():
    res = client.post("/api/v1/simulations/reset")
    assert res.status_code == 200
    assert res.json()["status"] == "success"

