import pytest
import hmac
import hashlib
import json
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.database.connection import SessionLocal
from app.database.models.user import User
from app.database.models.incident import Incident
from app.database.models.report import Report
from app.database.models.notification import NotificationOutbox
from app.database.models.whatsapp import WhatsAppUserLink, WhatsAppConversation, WhatsAppMessageLog
from app.services.whatsapp_service import whatsapp_service
from app.services.whatsapp_ticket_service import whatsapp_ticket_service
from app.services.whatsapp_conversation_service import whatsapp_conversation_service
from app.services.whatsapp_ai_client import whatsapp_ai_client
from app.services.whatsapp_qa_service import whatsapp_qa_service, FALLBACK_RESPONSE
from app.services.whatsapp_message_processor import whatsapp_message_processor
from app.services.notification_service import notification_service

client = TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------------------------
# 1. WhatsApp Webhook Tests
# -------------------------------------------------------------
def test_whatsapp_webhook_verification_success():
    """Verifies that Meta's webhook subscription handshake succeeds with valid verify token."""
    res = client.get(
        "/api/v1/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.WHATSAPP_VERIFY_TOKEN,
            "hub.challenge": "1158201444"
        }
    )
    assert res.status_code == 200
    assert res.text == "1158201444"

def test_whatsapp_webhook_verification_failure():
    """Verifies that webhook handshake rejects incorrect verification tokens."""
    res = client.get(
        "/api/v1/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "1158201444"
        }
    )
    assert res.status_code == 403

def test_whatsapp_webhook_signature_verification(monkeypatch):
    """Verifies X-Hub-Signature-256 HMAC calculation and rejection of forged signatures."""
    monkeypatch.setattr(whatsapp_service, "app_secret", "test_meta_app_secret")

    body = b'{"object": "whatsapp_business_account"}'
    # Valid signature
    mac = hmac.new(b"test_meta_app_secret", body, hashlib.sha256).hexdigest()
    assert whatsapp_service.verify_signature(body, f"sha256={mac}") is True

    # Tampered body / invalid signature
    assert whatsapp_service.verify_signature(body, "sha256=invalidhex123456") is False
    assert whatsapp_service.verify_signature(body, None) is False

def test_whatsapp_webhook_incoming_message_deduplication(db_session):
    """Verifies duplicate Meta messages are detected via WhatsAppMessageLog."""
    msg_id = "wamid.test_dedup_001"
    # Clean prior test state
    db_session.query(WhatsAppMessageLog).filter(WhatsAppMessageLog.message_id == msg_id).delete()
    db_session.commit()

    assert whatsapp_service.is_message_duplicate(db_session, msg_id) is False

    whatsapp_service.log_message(
        db=db_session,
        message_id=msg_id,
        sender_phone="15550001",
        recipient_phone="CampusOps",
        direction="inbound",
        content="Test message"
    )
    assert whatsapp_service.is_message_duplicate(db_session, msg_id) is True

# -------------------------------------------------------------
# 2. AI Classification Tests
# -------------------------------------------------------------
@pytest.mark.anyio
async def test_qwen_classification_success():
    """Tests successful issue classification and entity extraction."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: {
                "intent": "REPORT_ISSUE",
                "category": "Classroom",
                "subcategory": "Projector",
                "location": {"building": "Engineering Block", "room": "204"},
                "description": "Projector in room 204 is not working",
                "priority_recommendation": "NORMAL",
                "confidence": 0.95,
                "missing_fields": [],
                "requires_clarification": False
            }
        )
        res = await whatsapp_ai_client.classify_message("Projector in room 204 is not working")
        assert res["intent"] == "REPORT_ISSUE"
        assert res["category"] == "Classroom"
        assert res["location"]["room"] == "204"

@pytest.mark.anyio
async def test_ai_service_offline_fallback():
    """Verifies that if the local AI service / ngrok tunnel is offline, fallback rule-based classification takes over."""
    with patch("httpx.AsyncClient.post", side_effect=Exception("Connection refused")):
        res = await whatsapp_ai_client.classify_message("The AC is broken in room 101")
        assert res["intent"] == "REPORT_ISSUE"
        assert res["category"] == "HVAC"
        assert res["location"]["room"] == "101"

# -------------------------------------------------------------
# 3. Two-Step Phone Linking & Identity Verification
# -------------------------------------------------------------
def test_user_phone_linking_workflow(db_session):
    """Tests link code generation, verification, and unverified sender protection."""
    student = db_session.query(User).filter(User.role == "student").first()
    assert student is not None

    test_phone = "15559876543"

    # Clean old links
    db_session.query(WhatsAppUserLink).filter(WhatsAppUserLink.phone_number == test_phone).delete()
    db_session.commit()

    # Step 1: Generate 6-digit link code
    link_info = whatsapp_ticket_service.generate_link_code(db_session, student, test_phone)
    code = link_info["link_code"]
    assert len(code) == 6

    # Step 2: Verification fails with wrong code
    assert whatsapp_ticket_service.verify_link_code(db_session, test_phone, "000000") is None

    # Step 3: Verification succeeds with correct code
    verified_user = whatsapp_ticket_service.verify_link_code(db_session, test_phone, code)
    assert verified_user is not None
    assert verified_user.id == student.id

    # Step 4: User lookup by phone returns verified account
    looked_up = whatsapp_ticket_service.get_user_by_phone(db_session, test_phone)
    assert looked_up.id == student.id

# -------------------------------------------------------------
# 4. Ticket Automation Workflow & Ownership Enforcement
# -------------------------------------------------------------
def test_ticket_creation_from_whatsapp(db_session):
    """Tests creating real CampusOps Incident and Report records from WhatsApp."""
    student = db_session.query(User).filter(User.role == "student").first()

    data = {
        "category": "Electrical",
        "description": "Flickering lights and faulty socket",
        "location": {"room": "LIB-301", "building": "Library Block"},
        "priority_recommendation": "HIGH"
    }

    incident = whatsapp_ticket_service.create_ticket_from_whatsapp(db_session, student, data)
    assert incident.id is not None
    assert incident.incident_code.startswith("COP-")
    assert incident.category == "electrical"
    assert incident.priority == "P2"

    # Verify Report was created and linked
    report = db_session.query(Report).filter(Report.incident_id == incident.id).first()
    assert report is not None
    assert report.source == "whatsapp"
    assert report.reporter_id == student.id
    assert report.contact_phone == student.phone_number

    # Verify WorkOrder was created and linked
    from app.database.models.work_order import WorkOrder
    work_order = db_session.query(WorkOrder).filter(WorkOrder.incident_id == incident.id).first()
    assert work_order is not None
    assert work_order.incident_id == incident.id
    assert incident.status in ["open", "assigned"]

def test_ticket_ownership_access_control(db_session):
    """Verifies students cannot access other students' private tickets."""
    students = db_session.query(User).filter(User.role == "student").limit(2).all()
    if len(students) < 2:
        pytest.skip("Requires 2 students for ownership test")

    student_a, student_b = students[0], students[1]

    # Create ticket for student A
    data = {"category": "Classroom", "description": "Microphone dead", "location": {"room": "104"}}
    inc = whatsapp_ticket_service.create_ticket_from_whatsapp(db_session, student_a, data)

    # Student A can inspect it
    res_a = whatsapp_ticket_service.query_user_tickets(db_session, student_a, inc.incident_code)
    assert "Ticket Details" in res_a

    # Student B is rejected
    res_b = whatsapp_ticket_service.query_user_tickets(db_session, student_b, inc.incident_code)
    assert "restricted" in res_b

# -------------------------------------------------------------
# 5. Real-Time Status Notifications via Outbox
# -------------------------------------------------------------
def test_real_time_status_notification_outbox(db_session):
    """Verifies that ticket status changes place events into the transactional outbox with idempotency."""
    student = db_session.query(User).filter(User.role == "student").first()
    phone = "15554443322"
    student.phone_number = phone
    student.whatsapp_verified = True
    # Ensure any existing link reflects this phone
    existing_link = db_session.query(WhatsAppUserLink).filter(WhatsAppUserLink.user_id == student.id).first()
    if existing_link:
        existing_link.phone_number = phone
        existing_link.is_verified = True
    db_session.commit()

    # Create ticket
    data = {"category": "HVAC", "description": "AC blowing hot air", "location": {"room": "LIB-301"}}
    inc = whatsapp_ticket_service.create_ticket_from_whatsapp(db_session, student, data)

    # Trigger status update: Work in Progress
    notification_service.notify_ticket_state_change(db_session, inc.id, "in_progress")
    db_session.commit()

    # Verify outbox item exists
    outbox_item = (
        db_session.query(NotificationOutbox)
        .filter(
            NotificationOutbox.channel == "whatsapp",
            NotificationOutbox.recipient_phone == phone,
            NotificationOutbox.idempotency_key == f"wa_ticket_{inc.incident_code}_in_progress_{student.id}"
        )
        .first()
    )
    assert outbox_item is not None
    assert "Work in Progress" in outbox_item.body

    # Verify duplicate state change does not create duplicate outbox entries
    notification_service.notify_ticket_state_change(db_session, inc.id, "in_progress")
    db_session.commit()
    count = (
        db_session.query(NotificationOutbox)
        .filter(NotificationOutbox.idempotency_key == f"wa_ticket_{inc.incident_code}_in_progress_{student.id}")
        .count()
    )
    assert count == 1

# -------------------------------------------------------------
# 6. Question Answering & Fixed Fallback Response
# -------------------------------------------------------------
@pytest.mark.anyio
async def test_qa_campusops_database_retrieval(db_session):
    """Tests answering queries using live CampusOps database entities."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: {
                "answer": "Room LIB-301 is located in the Library Block and is currently confirmed ready.",
                "grounded": True,
                "source_refs": ["https://campusops.edu/facilities/campus-map"],
                "fallback_required": False
            }
        )
        ans = await whatsapp_qa_service.answer_query(db_session, "Where is room LIB-301 located?")
        assert "LIB-301" in ans

@pytest.mark.anyio
async def test_qa_institutional_knowledge_retrieval(db_session):
    """Tests answering verified institutional knowledge queries (e.g. library hours)."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: {
                "answer": "The Central Library is open Monday to Saturday from 08:00 AM to 10:00 PM.",
                "grounded": True,
                "source_refs": ["https://campusops.edu/library/timings-and-guidelines"],
                "fallback_required": False
            }
        )
        ans = await whatsapp_qa_service.answer_query(db_session, "What are the library timings?")
        assert "08:00 AM to 10:00 PM" in ans

@pytest.mark.anyio
async def test_qa_no_reliable_information_fallback(db_session):
    """Verifies that queries with no reliable context return the exact predefined fallback response."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: {
                "answer": FALLBACK_RESPONSE,
                "grounded": False,
                "source_refs": [],
                "fallback_required": True
            }
        )
        ans = await whatsapp_qa_service.answer_query(db_session, "What is the secret recipe for Martian space soup?")
        assert ans == FALLBACK_RESPONSE


# -------------------------------------------------------------
# 7. Simulator Unified Pipeline Tests
# -------------------------------------------------------------
def test_whatsapp_simulate_endpoint_multiturn_flow(db_session):
    """Verifies /simulate endpoint uses the authoritative message processor and creates real tickets."""
    student = db_session.query(User).filter(User.role == "student").first()
    phone = "15557778899"
    student.phone_number = phone
    student.whatsapp_verified = True
    db_session.commit()

    # Step 1: Greeting
    res1 = client.post("/api/v1/whatsapp/simulate", json={"from_phone": phone, "message": "Hi"})
    assert res1.status_code == 200
    assert "CampusOps" in res1.json()["reply"]

    # Step 2: Report issue with location
    res2 = client.post("/api/v1/whatsapp/simulate", json={"from_phone": phone, "message": "Projector not working in Room 204"})
    assert res2.status_code == 200
    assert "Shall I register this issue?" in res2.json()["reply"]
    assert res2.json()["session_step"] == "AWAITING_CONFIRMATION"

    # Step 3: Confirm registration
    res3 = client.post("/api/v1/whatsapp/simulate", json={"from_phone": phone, "message": "Yes"})
    assert res3.status_code == 200
    data3 = res3.json()
    assert "Your issue has been registered successfully." in data3["reply"]
    assert "Ticket ID: COP-" in data3["reply"]
    assert "Location:" in data3["reply"]
    assert "Status:" in data3["reply"]
    assert data3["session_step"] == "IDLE"
