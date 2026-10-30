from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_prevent_double_booking():
    login_res = client.post("/api/v1/auth/login", json={
        "email": "faculty@campusops.edu",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    rooms_res = client.get("/api/v1/rooms?status=available&limit=5", headers=headers)
    room_id = rooms_res.json()[0]["id"]

    start = (datetime.utcnow() + timedelta(days=20)).replace(hour=10, minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=2)

    # First booking succeeds
    bkg1 = client.post("/api/v1/bookings", json={
        "room_id": room_id,
        "title": "Robotics Guest Lecture",
        "purpose": "lecture",
        "start_time": start.isoformat(),
        "end_time": end.isoformat()
    }, headers={"Authorization": f"Bearer {token}"})
    assert bkg1.status_code == 200

    # Overlapping booking must fail with 409 Conflict
    bkg2 = client.post("/api/v1/bookings", json={
        "room_id": room_id,
        "title": "Conflicting Booking Attempt",
        "purpose": "seminar",
        "start_time": (start + timedelta(minutes=30)).isoformat(),
        "end_time": (end + timedelta(minutes=30)).isoformat()
    }, headers={"Authorization": f"Bearer {token}"})
    assert bkg2.status_code == 409
