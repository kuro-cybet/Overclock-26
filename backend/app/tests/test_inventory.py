from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_inventory_listing():
    res = client.get("/api/v1/inventory")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 35

def test_prevent_over_reservation():
    # Attempt to reserve 9999 units of an item
    inv_res = client.get("/api/v1/inventory?limit=1")
    item = inv_res.json()[0]

    res = client.post("/api/v1/inventory/reserve", json={
        "work_order_id": "test_wo_id",
        "item_id": item["id"],
        "quantity": 999999
    })
    assert res.status_code == 409
    assert "Only" in res.json()["detail"] or "Cannot reserve" in res.json()["detail"]

