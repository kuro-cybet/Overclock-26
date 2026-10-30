import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.database.models.work_order import WorkOrder
from app.database.models.work_order_checklist import WorkOrderChecklistItem
from app.database.models.inventory import InventoryItem
from app.database.models.inventory_transaction import InventoryTransaction
from app.database.models.booking import RoomBooking
from app.database.models.notification import NotificationOutbox
from app.database.models.user import User
from app.services.notification_service import notification_service

client = TestClient(app)

def get_token(email: str, password: str = "password123") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def test_checklist_persistence_and_enforcement():
    tech_token = get_token("tech@campusops.edu")
    headers = {"Authorization": f"Bearer {tech_token}"}

    # 1. Fetch work orders
    wo_res = client.get("/api/v1/work-orders", headers=headers)
    assert wo_res.status_code == 200
    work_orders = wo_res.json()
    assert len(work_orders) > 0

    target_wo = None
    for wo in work_orders:
        if wo["status"] == "in_progress":
            target_wo = wo
            break
    if not target_wo:
        for wo in work_orders:
            if wo["status"] == "assigned":
                target_wo = wo
                # Transition to in_progress first
                client.patch(f"/api/v1/work-orders/{wo['id']}", json={"status": "in_progress"}, headers=headers)
                break
    if not target_wo:
        target_wo = work_orders[0]
        # Force set status to in_progress in DB to test checklist enforcement
        db = SessionLocal()
        db_wo = db.query(WorkOrder).filter(WorkOrder.id == target_wo["id"]).first()
        db_wo.status = "in_progress"
        db.commit()
        db.close()

    wo_id = target_wo["id"]

    # 2. Get checklist items
    cl_res = client.get(f"/api/v1/work-orders/{wo_id}/checklist", headers=headers)
    assert cl_res.status_code == 200
    checklist = cl_res.json()
    assert isinstance(checklist, list)
    assert len(checklist) > 0

    first_item = checklist[0]
    item_id = first_item["id"]

    # 3. Mark task as completed
    patch_res = client.patch(
        f"/api/v1/work-orders/{wo_id}/checklist/{item_id}",
        json={"is_completed": True},
        headers=headers
    )
    assert patch_res.status_code == 200
    updated_item = patch_res.json()
    assert updated_item["is_completed"] is True
    assert updated_item["completed_at"] is not None

    # 4. Enforce checklist completion before work order sign-off
    db = SessionLocal()
    uncompleted = (
        db.query(WorkOrderChecklistItem)
        .filter(
            WorkOrderChecklistItem.work_order_id == wo_id,
            WorkOrderChecklistItem.is_completed == False
        )
        .count()
    )
    db.close()

    if uncompleted > 0:
        complete_res = client.patch(
            f"/api/v1/work-orders/{wo_id}",
            json={"status": "completed"},
            headers=headers
        )
        assert complete_res.status_code == 422
        assert "Cannot complete work order" in complete_res.json()["detail"]


def test_parts_requisition_flow():
    tech_token = get_token("tech@campusops.edu")
    headers = {"Authorization": f"Bearer {tech_token}"}

    # Fetch active work order
    wo_res = client.get("/api/v1/work-orders", headers=headers)
    wo_id = wo_res.json()[0]["id"]

    # Fetch inventory item
    inv_res = client.get("/api/v1/inventory?limit=5", headers=headers)
    inv_items = inv_res.json()
    assert len(inv_items) > 0
    item = inv_items[0]

    # Requisition 1 unit
    req_res = client.post(
        f"/api/v1/work-orders/{wo_id}/parts-requisition",
        json={
            "item_id": item["id"],
            "quantity": 1,
            "urgency": "normal",
            "justification": "Field replacement of faulty component"
        },
        headers=headers
    )
    assert req_res.status_code == 200
    res_data = req_res.json()
    assert res_data["status"] in ["reserved", "procurement_requested", "blocked_awaiting_procurement"]
    assert res_data["work_order_id"] == wo_id


def test_technician_cannot_directly_modify_inventory():
    tech_token = get_token("tech@campusops.edu")
    headers = {"Authorization": f"Bearer {tech_token}"}

    # Fetch inventory item
    inv_res = client.get("/api/v1/inventory?limit=1", headers=headers)
    item_id = inv_res.json()[0]["id"]

    # Technician attempting direct PATCH to update quantity
    mod_res = client.patch(
        f"/api/v1/inventory/{item_id}",
        json={"current_stock": 9999},
        headers=headers
    )
    # Must be 403 Forbidden or 405 Method Not Allowed (direct stock manipulation prohibited)
    assert mod_res.status_code in [403, 404, 405]


def test_faculty_examination_readiness():
    faculty_token = get_token("faculty@campusops.edu")
    headers = {"Authorization": f"Bearer {faculty_token}"}

    # Query examination bookings
    exam_res = client.get("/api/v1/bookings/examinations", headers=headers)
    assert exam_res.status_code == 200
    exams = exam_res.json()
    assert isinstance(exams, list)

    if len(exams) > 0:
        booking_id = exams[0]["id"]
        # Submit readiness inspection result
        inspect_res = client.post(
            f"/api/v1/bookings/{booking_id}/exam-readiness",
            json={
                "status": "ready",
                "notes": "Physical inspection verified by presiding faculty. Hall desks and lighting checked.",
                "checklist": {
                    "hvac_check": True,
                    "power_check": True,
                    "seating_check": True,
                    "av_check": True
                }
            },
            headers=headers
        )
        assert inspect_res.status_code == 200
        result = inspect_res.json()
        assert result["readiness_status"] == "ready"
        assert result["booking_id"] == booking_id


def test_student_request_submission():
    student_token = get_token("student@campusops.edu")
    headers = {"Authorization": f"Bearer {student_token}"}

    db = SessionLocal()
    user = db.query(User).filter(User.email == "student@campusops.edu").first()
    building_id = user.building_id if user else "bld-01"
    db.close()

    report_payload = {
        "title": "Air Conditioner Leaking in Study Room",
        "description": "Continuous water droplet leakage near the electrical outlet.",
        "category": "hvac",
        "urgency": "medium",
        "building_id": building_id or "bld-01"
    }

    res = client.post("/api/v1/reports", json=report_payload, headers=headers)
    assert res.status_code in [200, 201]
    data = res.json()
    assert "report_code" in data or "id" in data


def test_role_based_access_controls():
    tech_token = get_token("tech@campusops.edu")
    faculty_token = get_token("faculty@campusops.edu")
    admin_token = get_token("admin@campusops.edu")

    # 1. Technician cannot directly execute recovery
    tech_rec_res = client.post(
        "/api/v1/recovery/execute",
        json={"target_action": "test", "action_payload": {}},
        headers={"Authorization": f"Bearer {tech_token}"}
    )
    assert tech_rec_res.status_code == 403

    # 2. Faculty cannot override approvals
    fac_app_res = client.post(
        "/api/v1/approvals/non-existent-id/decision",
        json={"decision": "approved", "decision_reason": "Faculty override"},
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert fac_app_res.status_code in [403, 404]

    # 3. Technician cannot directly reassign work orders (only admin can)
    wo_res = client.get("/api/v1/work-orders", headers={"Authorization": f"Bearer {admin_token}"})
    wo_id = wo_res.json()[0]["id"]

    tech_reassign = client.post(
        f"/api/v1/work-orders/{wo_id}/reassign",
        json={"new_technician_id": "tech-002", "reassignment_reason": "Direct reassign attempt"},
        headers={"Authorization": f"Bearer {tech_token}"}
    )
    assert tech_reassign.status_code == 403


def test_notification_outbox_retry_and_backoff():
    db = SessionLocal()
    # Create test outbox item
    test_outbox = NotificationOutbox(
        recipient_email="test.retry@campusops.edu",
        channel="email",
        subject="Retry Test Subject",
        body="Testing retry and exponential backoff",
        event_type="report_submitted",
        status="queued",
        attempts=1,
        last_attempt_at=datetime.utcnow()  # Just attempted, should be skipped due to 10s backoff
    )
    db.add(test_outbox)
    db.commit()
    db.refresh(test_outbox)
    test_id = test_outbox.id

    try:
        # Process pending outbox
        result = notification_service.process_pending_outbox(db=db, max_items=50)
        assert result["skipped_backoff"] >= 1

        # Check item status still queued and attempts remained 1 (backoff respected)
        refreshed = db.query(NotificationOutbox).filter(NotificationOutbox.id == test_id).first()
        assert refreshed.status == "queued"
        assert refreshed.attempts == 1

        # Simulate elapsed time beyond backoff
        refreshed.last_attempt_at = datetime.utcnow() - timedelta(seconds=15)
        db.commit()

        # Re-process: now it should proceed
        result2 = notification_service.process_pending_outbox(db=db, max_items=50)
        refreshed2 = db.query(NotificationOutbox).filter(NotificationOutbox.id == test_id).first()
        assert result2["sent"] == 0
        assert result2["simulated"] >= 1
        assert refreshed2.status == "simulated"
        assert refreshed2.attempts == 2

    finally:
        # Clean up test record
        db.query(NotificationOutbox).filter(NotificationOutbox.id == test_id).delete()
        db.commit()
        db.close()


def test_recovery_execution_failure_handling():
    admin_token = get_token("admin@campusops.edu")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Calling run-actions on a non-existent execution should raise 404
    missing_res = client.post(
        "/api/v1/recovery/non-existent-exec-id/run-actions",
        headers=headers
    )
    assert missing_res.status_code == 404

    # 2. Calling verify on a non-existent execution should raise 404
    missing_ver_res = client.post(
        "/api/v1/recovery/non-existent-exec-id/verify",
        headers=headers
    )
    assert missing_ver_res.status_code == 404

    # 3. List executions returns a valid list
    list_res = client.get("/api/v1/recovery/executions", headers=headers)
    assert list_res.status_code == 200
    assert isinstance(list_res.json(), list)


def test_duplicate_event_handling():
    tech_token = get_token("tech@campusops.edu")
    headers = {"Authorization": f"Bearer {tech_token}"}

    # 1. Fetch work orders and target checklist item
    wo_res = client.get("/api/v1/work-orders", headers=headers)
    wo_id = wo_res.json()[0]["id"]
    cl_res = client.get(f"/api/v1/work-orders/{wo_id}/checklist", headers=headers)
    item_id = cl_res.json()[0]["id"]

    # 2. Mark item completed first time
    res1 = client.patch(
        f"/api/v1/work-orders/{wo_id}/checklist/{item_id}",
        json={"is_completed": True},
        headers=headers
    )
    assert res1.status_code == 200
    first_completed_at = res1.json()["completed_at"]

    # 3. Send duplicate completion event -> Idempotent handling
    res2 = client.patch(
        f"/api/v1/work-orders/{wo_id}/checklist/{item_id}",
        json={"is_completed": True},
        headers=headers
    )
    assert res2.status_code == 200
    assert res2.json()["is_completed"] is True

    # 4. Outbox duplicate prevention: items in "sent" state are never re-processed
    db = SessionLocal()
    sent_outbox = NotificationOutbox(
        recipient_email="already.sent@campusops.edu",
        channel="email",
        subject="Already Delivered",
        body="Duplicate prevention test",
        event_type="report_submitted",
        status="sent",
        attempts=1,
        last_attempt_at=datetime.utcnow()
    )
    db.add(sent_outbox)
    db.commit()
    sent_id = sent_outbox.id

    try:
        # Run outbox processing
        batch = notification_service.process_pending_outbox(db=db, max_items=25)
        refreshed = db.query(NotificationOutbox).filter(NotificationOutbox.id == sent_id).first()
        # Must remain untouched with status="sent" and attempts=1
        assert refreshed.status == "sent"
        assert refreshed.attempts == 1
    finally:
        db.query(NotificationOutbox).filter(NotificationOutbox.id == sent_id).delete()
        db.commit()
        db.close()
