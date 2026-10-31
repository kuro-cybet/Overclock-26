import uuid

from fastapi.testclient import TestClient
from sqlalchemy import or_

from app.database.connection import SessionLocal
from app.database.models.campus import Building
from app.database.models.asset import Asset
from app.database.models.notification import Notification
from app.database.models.report import Report
from app.database.models.room import Room
from app.database.models.user import User
from app.main import app

client = TestClient(app)


def _token(email: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _headers(email: str) -> dict:
    return {"Authorization": f"Bearer {_token(email)}"}


def test_technician_room_readiness_updates_freshness_metadata():
    room_id = str(uuid.uuid4())
    room = Room(
        id=room_id,
        building_id=str(uuid.uuid4()),
        floor_id=str(uuid.uuid4()),
        room_number=f"QR-{room_id[:8]}",
        name="QR Readiness Test Room",
        type="classroom",
        capacity=20,
        status="available",
    )
    db = SessionLocal()
    db.add(room)
    db.commit()
    db.close()

    try:
        headers = _headers("tech@campusops.edu")
        working = client.patch(
            f"/api/v1/rooms/{room_id}/readiness",
            json={"daily_readiness_status": "confirmed_today"},
            headers=headers,
        )
        assert working.status_code == 200, working.text
        assert working.json()["daily_readiness_status"] == "confirmed_today"
        assert working.json()["freshness_state"] == "confirmed_today"
        assert working.json()["freshness_source"] == "technician_qr"
        assert working.json()["readiness_checked_by"]
        assert working.json()["last_confirmed_at"]

        stale = client.patch(
            f"/api/v1/rooms/{room_id}/readiness",
            json={"daily_readiness_status": "stale"},
            headers=headers,
        )
        assert stale.status_code == 200, stale.text
        assert stale.json()["daily_readiness_status"] == "stale"
        assert stale.json()["freshness_state"] == "stale"
        assert stale.json()["last_confirmed_at"]
    finally:
        db = SessionLocal()
        db.query(Room).filter(Room.id == room_id).delete()
        db.commit()
        db.close()


def test_technician_can_resolve_a_device_asset_tag_from_its_physical_qr():
    suffix = uuid.uuid4().hex[:8]
    building = Building(
        name=f"QR Asset Test Building {suffix}",
        code=f"QRA{suffix[:5]}",
        total_floors=1,
    )
    db = SessionLocal()
    db.add(building)
    db.flush()
    room = Room(
        building_id=building.id,
        floor_id=str(uuid.uuid4()),
        room_number=f"QR-{suffix}",
        name="QR Asset Test Classroom",
        type="classroom",
        capacity=20,
        status="available",
    )
    db.add(room)
    db.flush()
    asset = Asset(
        asset_tag=f"DEVICE-{suffix}",
        name="Classroom projector",
        category="av_equipment",
        building_id=building.id,
        room_id=room.id,
        status="operational",
    )
    db.add(asset)
    db.commit()
    asset_id = asset.id
    asset_tag = asset.asset_tag
    room_id = room.id
    building_id = building.id
    db.close()

    try:
        response = client.get(
            f"/api/v1/assets/qr/{asset_tag}",
            headers=_headers("tech@campusops.edu"),
        )
        assert response.status_code == 200, response.text
        assert response.json()["id"] == asset_id
        assert response.json()["room_id"] == room_id
    finally:
        db = SessionLocal()
        db.query(Asset).filter(Asset.id == asset_id).delete()
        db.query(Room).filter(Room.id == room_id).delete()
        db.query(Building).filter(Building.id == building_id).delete()
        db.commit()
        db.close()


def test_admin_broadcast_reaches_active_non_mock_users():
    title = f"Test campus notice {uuid.uuid4()}"
    db = SessionLocal()
    active_users = db.query(User).filter(
        User.is_active.is_(True),
        or_(User.auth_provider.is_(None), User.auth_provider != "mock"),
    )
    expected_recipient_count = active_users.count()
    expected_roles = {user.role for user in active_users.all()}
    db.close()

    response = client.post(
        "/api/v1/notifications/broadcast",
        json={
            "title": title,
            "message": "Test announcement.",
            "type": "info",
        },
        headers=_headers("admin@campusops.edu"),
    )
    assert response.status_code == 200, response.text

    db = SessionLocal()
    try:
        created = db.query(Notification).filter(Notification.title == title).all()
        assert {notification.recipient_role for notification in created} == expected_roles
        assert response.json()["created_count"] == len(expected_roles)
        assert response.json()["recipient_count"] == expected_recipient_count
    finally:
        db.query(Notification).filter(Notification.title == title).delete()
        db.commit()
        db.close()

    forbidden = client.post(
        "/api/v1/notifications/broadcast",
        json={"title": title, "message": "No."},
        headers=_headers("student@campusops.edu"),
    )
    assert forbidden.status_code == 403


def test_report_list_includes_reporter_and_location_details():
    suffix = uuid.uuid4().hex[:8]
    building = Building(
        name=f"QR Report Test Building {suffix}",
        code=f"QRT{suffix[:5]}",
        total_floors=1,
    )
    reporter = User(
        email=f"qr-report-{suffix}@example.invalid",
        hashed_password="!",
        name="QR Report Test Reporter",
        role="faculty",
        auth_provider="mock",
        is_active=True,
    )
    db = SessionLocal()
    db.add_all([building, reporter])
    db.flush()
    room = Room(
        building_id=building.id,
        floor_id=str(uuid.uuid4()),
        room_number=f"R-{suffix}",
        name="QR Report Test Room",
        type="classroom",
        capacity=20,
        status="available",
    )
    db.add(room)
    db.flush()
    report = Report(
        report_code=f"RPT-QR-{suffix}",
        title="Projector has no signal",
        description="The display shows no input when the projector is switched on.",
        category="equipment",
        urgency="medium",
        building_id=building.id,
        room_id=room.id,
        reporter_id=reporter.id,
        reporter_role="faculty",
        source="web_portal",
        status="submitted",
    )
    db.add(report)
    db.commit()
    report_id = report.id
    room_id = room.id
    building_id = building.id
    reporter_id = reporter.id
    expected_building_name = building.name
    expected_room_number = room.room_number
    db.close()

    try:
        response = client.get(
            "/api/v1/reports?status=submitted",
            headers=_headers("admin@campusops.edu"),
        )
        assert response.status_code == 200, response.text
        report_body = next(item for item in response.json() if item["id"] == report_id)
        assert report_body["reporter_name"] == "QR Report Test Reporter"
        assert report_body["building_name"] == expected_building_name
        assert report_body["room_number"] == expected_room_number
        assert report_body["room_name"] == "QR Report Test Room"
        assert "no input" in report_body["description"]
    finally:
        db = SessionLocal()
        db.query(Report).filter(Report.id == report_id).delete()
        db.query(Room).filter(Room.id == room_id).delete()
        db.query(User).filter(User.id == reporter_id).delete()
        db.query(Building).filter(Building.id == building_id).delete()
        db.commit()
        db.close()
