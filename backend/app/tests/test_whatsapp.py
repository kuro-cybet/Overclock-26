import json
import uuid
import hmac
import hashlib
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.database.connection import SessionLocal
from app.database.models.whatsapp import WhatsAppMessageLog, WhatsAppSession
from app.database.models.report import Report
from app.database.models.incident import Incident
from app.database.models.work_order import WorkOrder
from app.database.models.user import User
from app.database.models.notification import NotificationOutbox

client = TestClient(app)

def test_whatsapp_webhook_verification_success():
    """Verify Meta Webhook GET challenge verification with valid token."""
    challenge_val = "1158201444"
    res = client.get(
        "/api/v1/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.WHATSAPP_VERIFY_TOKEN,
            "hub.challenge": challenge_val
        }
    )
    assert res.status_code == 200
    assert res.text == challenge_val

def test_whatsapp_webhook_verification_failure():
    """Verify Meta Webhook GET rejects wrong verify token."""
    res = client.get(
        "/api/v1/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_invalid_token",
            "hub.challenge": "12345"
        }
    )
    assert res.status_code == 403

def test_whatsapp_webhook_signature_verification():
    """Verify HMAC-SHA256 signature verification."""
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "10001",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "1555000", "phone_number_id": "1001"},
                    "contacts": [{"profile": {"name": "Jordan"}, "wa_id": "15554000001"}],
                    "messages": [{
                        "from": "15554000001",
                        "id": "wamid.test_sig_001",
                        "timestamp": "1730000000",
                        "text": {"body": "hello"},
                        "type": "text"
                    }]
                }
            }]
        }]
    }
    raw_bytes = json.dumps(payload).encode("utf-8")

    secret = settings.WHATSAPP_APP_SECRET or "test_secret_for_suite"
    orig_secret = settings.WHATSAPP_APP_SECRET
    settings.WHATSAPP_APP_SECRET = secret

    try:
        valid_sig = "sha256=" + hmac.new(secret.encode("utf-8"), raw_bytes, hashlib.sha256).hexdigest()
        res = client.post(
            "/api/v1/whatsapp/webhook",
            content=raw_bytes,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": valid_sig}
        )
        assert res.status_code == 200

        invalid_sig = "sha256=badbadbadbadbadbadbadbadbadbad"
        res_bad = client.post(
            "/api/v1/whatsapp/webhook",
            content=raw_bytes,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": invalid_sig}
        )
        assert res_bad.status_code == 403
    finally:
        settings.WHATSAPP_APP_SECRET = orig_secret

def test_whatsapp_message_deduplication():
    """Verify idempotency: duplicate WhatsApp message_id is ignored without reprocessing."""
    msg_id = f"wamid.idempotent_{uuid.uuid4().hex[:8]}"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "10001",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "1555000", "phone_number_id": "1001"},
                    "contacts": [{"profile": {"name": "Jordan"}, "wa_id": "15554000001"}],
                    "messages": [{
                        "from": "15554000001",
                        "id": msg_id,
                        "timestamp": "1730000000",
                        "text": {"body": "Testing duplicate prevention"},
                        "type": "text"
                    }]
                }
            }]
        }]
    }

    res1 = client.post("/api/v1/whatsapp/webhook", json=payload)
    assert res1.status_code == 200

    db = SessionLocal()
    try:
        count_first = db.query(WhatsAppMessageLog).filter(WhatsAppMessageLog.message_id == msg_id).count()
        assert count_first == 1

        res2 = client.post("/api/v1/whatsapp/webhook", json=payload)
        assert res2.status_code == 200

        count_second = db.query(WhatsAppMessageLog).filter(WhatsAppMessageLog.message_id == msg_id).count()
        assert count_second == 1
    finally:
        db.close()

def test_complaint_registration_multi_turn_flow():
    """
    Test end-to-end complaint registration with multi-turn slot filling:
    User: "The projector in Room 204 is not working."
    Bot: asks which building
    User: "Block A" (or Science Block)
    Bot: asks detail
    User: "Completely not working."
    Bot: registers complaint and outputs CMP-XXXX with location and status.
    """
    phone = f"+1555{uuid.uuid4().int % 9000000 + 1000000}"

    # Step 1: Initial complaint (missing building)
    res1 = client.post("/api/v1/whatsapp/simulate", json={
        "from_phone": phone,
        "message": "Hello, the projector in Room 204 is not working."
    })
    assert res1.status_code == 200
    data1 = res1.json()
    assert "Which building" in data1["reply"] or "building" in data1["reply"].lower()
    assert data1["session_step"] == "AWAITING_BUILDING"

    # Step 2: User provides building
    res2 = client.post("/api/v1/whatsapp/simulate", json={
        "from_phone": phone,
        "message": "Science Block"
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert "working" in data2["reply"].lower() or "occasional" in data2["reply"].lower()
    assert data2["session_step"] == "AWAITING_DETAILS"

    # Step 3: User provides status details
    res3 = client.post("/api/v1/whatsapp/simulate", json={
        "from_phone": phone,
        "message": "Completely not working."
    })
    assert res3.status_code == 200
    data3 = res3.json()
    reply = data3["reply"]
    assert "registered successfully" in reply
    assert "CMP-" in reply
    assert "Science Block" in reply
    assert "Status: Submitted" in reply
    assert data3["session_step"] == "IDLE"

    # Verify complaint in database
    db = SessionLocal()
    try:
        clean_p = phone.replace("+", "")
        rep = db.query(Report).filter(Report.contact_phone.like(f"%{clean_p}%")).order_by(Report.created_at.desc()).first()
        assert rep is not None
        assert rep.source == "whatsapp"
        assert "projector" in rep.description.lower()
    finally:
        db.close()

def test_campus_information_queries():
    """Test grounded campus inquiries (HOD, faculty, library, classroom availability)."""
    # 1. HOD Query
    res_hod = client.post("/api/v1/whatsapp/simulate", json={
        "from_phone": "+15554000001",
        "message": "Who is the HOD of engineering?"
    })
    assert res_hod.status_code == 200
    assert "Arthur Pendelton" in res_hod.json()["reply"]

    # 2. Faculty office query
    res_fac = client.post("/api/v1/whatsapp/simulate", json={
        "from_phone": "+15554000001",
        "message": "Where is Prof Finch's office?"
    })
    assert res_fac.status_code == 200
    assert "Alistair Finch" in res_fac.json()["reply"]
    assert "Engineering Block" in res_fac.json()["reply"]

    # 3. Library location
    res_lib = client.post("/api/v1/whatsapp/simulate", json={
        "from_phone": "+15554000001",
        "message": "Where is the library and what facilities does it have?"
    })
    assert res_lib.status_code == 200
    assert "Library Block" in res_lib.json()["reply"]
    assert "Central Reading Room" in res_lib.json()["reply"]

    # 4. Classrooms available
    res_avail = client.post("/api/v1/whatsapp/simulate", json={
        "from_phone": "+15554000001",
        "message": "Which classrooms are available?"
    })
    assert res_avail.status_code == 200
    assert "available" in res_avail.json()["reply"].lower()

    # 5. Grounded truth test: Non-existent entity must not be hallucinated
    res_unknown = client.post("/api/v1/whatsapp/simulate", json={
        "from_phone": "+15554000001",
        "message": "Who is Dr. Ronald McDonald in the Magic Wand Department?"
    })
    assert res_unknown.status_code == 200
    assert "couldn't find" in res_unknown.json()["reply"].lower() or "helpdesk" in res_unknown.json()["reply"].lower()

def test_complaint_tracking_authorization():
    """Test authorized vs unauthorized complaint tracking."""
    db = SessionLocal()
    try:
        rand_code = f"CMP-TRK-{uuid.uuid4().hex[:6].upper()}"
        rpt_code = rand_code.replace("CMP-", "RPT-")
        student = db.query(User).filter(User.email == "student@campusops.edu").first()
        building = db.query(Report).first().building_id

        my_report = Report(
            report_code=rpt_code,
            title="Broken chair in study hall",
            description="Armrest broken off",
            category="furniture",
            urgency="low",
            building_id=building,
            reporter_id=student.id,
            reporter_role="student",
            source="whatsapp",
            contact_phone="+15554000001",
            status="submitted"
        )
        db.add(my_report)
        db.commit()

        # Authorized access from +15554000001
        res_auth = client.post("/api/v1/whatsapp/simulate", json={
            "from_phone": "+15554000001",
            "message": f"Track complaint {rand_code}"
        })
        assert res_auth.status_code == 200
        assert "Complaint Details:" in res_auth.json()["reply"]
        assert rand_code in res_auth.json()["reply"]
        assert "Submitted" in res_auth.json()["reply"]

        # Unauthorized access from unknown third-party (+15559999999)
        res_unauth = client.post("/api/v1/whatsapp/simulate", json={
            "from_phone": "+15559999999",
            "message": f"Track complaint {rand_code}"
        })
        assert res_unauth.status_code == 200
        assert "Unauthorized" in res_unauth.json()["reply"]

    finally:
        db.close()

def test_automatic_whatsapp_notifications_on_lifecycle():
    """
    Test that when an incident work order is assigned, starts work, and resolves,
    automatic WhatsApp notifications are sent to the complainant.
    """
    db = SessionLocal()
    try:
        # 1. Login as Admin
        login_res = client.post("/api/v1/auth/login", json={
            "email": "admin@campusops.edu",
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        test_phone = f"+1555{uuid.uuid4().int % 9000000 + 1000000}"

        # 2. Submit a complaint from a student via WhatsApp
        client.post("/api/v1/whatsapp/simulate", json={
            "from_phone": test_phone,
            "message": "The Wi-Fi in Computer Lab A is dropping continuously."
        })
        client.post("/api/v1/whatsapp/simulate", json={
            "from_phone": test_phone,
            "message": "Engineering Block"
        })
        rep_res = client.post("/api/v1/whatsapp/simulate", json={
            "from_phone": test_phone,
            "message": "Complete packet loss every 2 minutes."
        })
        assert "registered successfully" in rep_res.json()["reply"]

        clean_p = test_phone.replace("+", "")
        rep = db.query(Report).filter(Report.contact_phone.like(f"%{clean_p}%")).order_by(Report.created_at.desc()).first()
        assert rep is not None

        # Link to or create incident
        tech = db.query(User).filter(User.email == "tech@campusops.edu").first()
        incident = db.query(Incident).filter(Incident.room_id == rep.room_id).first()
        if not incident:
            incident = Incident(
                incident_code=f"INC-{uuid.uuid4().hex[:6].upper()}",
                title="Wi-Fi AP Outage",
                description="Reported by WhatsApp",
                category="network",
                building_id=rep.building_id,
                room_id=rep.room_id,
                status="open"
            )
            db.add(incident)
            db.commit()
            db.refresh(incident)

        rep.incident_id = incident.id
        db.commit()

        # 3. Create a work order assigned to technician David Miller
        wo_res = client.post("/api/v1/work-orders", json={
            "incident_id": incident.id,
            "title": "Repair Wi-Fi Access Point",
            "description": "Replace switch cable",
            "assigned_technician_id": tech.id,
            "priority": "P2"
        }, headers=headers)
        assert wo_res.status_code == 200
        wo_id = wo_res.json()["id"]

        # Check notification outbox for assignment notification
        assign_notif = db.query(NotificationOutbox).filter(
            NotificationOutbox.recipient_phone.like(f"%{clean_p}%"),
            NotificationOutbox.subject.like("%assigned%")
        ).first()
        assert assign_notif is not None
        assert "assigned to a technician" in assign_notif.body

        # 4. Technician starts work (PATCH status to in_progress)
        tech_login = client.post("/api/v1/auth/login", json={
            "email": "tech@campusops.edu",
            "password": "password123"
        })
        tech_token = tech_login.json()["access_token"]
        tech_headers = {"Authorization": f"Bearer {tech_token}"}

        patch_res = client.patch(f"/api/v1/work-orders/{wo_id}", json={
            "status": "in_progress",
            "diagnosis": "Loose ethernet patch cord."
        }, headers=tech_headers)
        assert patch_res.status_code == 200

        # Check notification outbox for in_progress notification
        prog_notif = db.query(NotificationOutbox).filter(
            NotificationOutbox.recipient_phone.like(f"%{clean_p}%"),
            NotificationOutbox.subject.like("%in_progress%")
        ).first()
        assert prog_notif is not None
        assert "now being addressed" in prog_notif.body

        # 5. Complete mandatory checklist items and mark completed
        from app.database.models.work_order_checklist import WorkOrderChecklistItem
        db.query(WorkOrderChecklistItem).filter(WorkOrderChecklistItem.work_order_id == wo_id).update({"is_completed": True})
        db.commit()

        done_res = client.patch(f"/api/v1/work-orders/{wo_id}", json={
            "status": "completed",
            "evidence_notes": "Cable replaced, AP rebooted."
        }, headers=tech_headers)
        assert done_res.status_code == 200

        # Check notification outbox for resolved notification
        done_notif = db.query(NotificationOutbox).filter(
            NotificationOutbox.recipient_phone.like(f"%{clean_p}%"),
            NotificationOutbox.subject.like("%resolved%")
        ).first()
        assert done_notif is not None
        assert "marked as resolved" in done_notif.body

    finally:
        db.close()

def test_conversation_reset_command():
    """Verify 'cancel' or 'reset' clears multi-turn conversation session."""
    phone = "+15554000088"
    client.post("/api/v1/whatsapp/simulate", json={
        "from_phone": phone,
        "message": "The AC is broken"
    })
    res_cancel = client.post("/api/v1/whatsapp/simulate", json={
        "from_phone": phone,
        "message": "cancel"
    })
    assert res_cancel.status_code == 200
    assert "Conversation reset" in res_cancel.json()["reply"]
    assert res_cancel.json()["session_step"] == "IDLE"
