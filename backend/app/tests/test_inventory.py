from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _tech_headers():
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "tech@campusops.edu", "password": "password123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_inventory_listing():
    res = client.get("/api/v1/inventory", headers=_tech_headers())
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 35

def test_prevent_over_reservation():
    headers = _tech_headers()
    # Attempt to reserve 9999 units of an item
    inv_res = client.get("/api/v1/inventory?limit=1", headers=headers)
    item = inv_res.json()[0]

    res = client.post("/api/v1/inventory/reserve", json={
        "work_order_id": "test_wo_id",
        "item_id": item["id"],
        "quantity": 999999
    }, headers=headers)
    assert res.status_code == 409
    assert "Only" in res.json()["detail"] or "Cannot reserve" in res.json()["detail"]
