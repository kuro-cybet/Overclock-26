from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

import app.database.models  # noqa: F401
import pytest
from app.api.deps import get_current_user
from app.database.base import Base
from app.database.connection import get_db
from app.database.models.campus import Building
from app.database.models.incident import Incident
from app.database.models.notification import NotificationOutbox
from app.database.models.report import Report
from app.database.models.user import User
from app.database.models.work_order import WorkOrder
from app.main import app
from app.services import workflow_notifications
from app.services.notification_service import notification_service


def test_email_is_sent_on_report_and_only_after_all_work_is_complete():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(bind=engine, autoflush=False)()

    reporter = User(
        email="reporter@example.com",
        hashed_password="!",
        name="Reporter",
        role="student",
    )
    admin = User(
        email="facilities@example.com",
        hashed_password="!",
        name="Facilities",
        role="admin",
        sub_role="facilities_admin",
    )
    technician = User(
        email="technician@example.com",
        hashed_password="!",
        name="Technician",
        role="technician",
    )
    building = Building(name="Test Building", code="TEST", total_floors=1)
    test_session.add_all([reporter, admin, technician, building])
    test_session.flush()

    report = Report(
        report_code="RPT-TEST-0001",
        title="Broken light",
        description="The room light is broken.",
        category="electrical",
        urgency="medium",
        building_id=building.id,
        reporter_id=reporter.id,
        reporter_role="student",
        source="web_portal",
        status="submitted",
    )
    test_session.add(report)
    test_session.flush()

    previous_overrides = app.dependency_overrides.copy()

    def override_db():
        yield test_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: technician

    try:
        workflow_notifications.report_submitted(test_session, report)
        test_session.commit()
        queued = test_session.query(NotificationOutbox).all()
        assert len(queued) == 2
        assert {item.event_type for item in queued} == {"report_submitted"}
        assert {item.recipient_email for item in queued} == {
            reporter.email,
            admin.email,
        }

        incident = Incident(
            incident_code="INC-TEST-0001",
            title=report.title,
            description=report.description,
            category=report.category,
            severity="medium",
            priority="P3",
            building_id=building.id,
            status="in_progress",
        )
        test_session.add(incident)
        test_session.flush()
        report.incident_id = incident.id
        work_orders = [
            WorkOrder(
                work_order_code=f"WO-TEST-000{i}",
                incident_id=incident.id,
                title=report.title,
                description=report.description,
                assigned_technician_id=technician.id,
                priority="P3",
                status="in_progress",
            )
            for i in (1, 2)
        ]
        test_session.add_all(work_orders)
        test_session.commit()

        workflow_notifications.report_triaged(
            test_session, report, incident, work_orders[0], technician
        )
        workflow_notifications.work_order_assigned(
            test_session, work_orders[0], incident, technician
        )
        workflow_notifications.work_order_created(
            test_session, work_orders[0], incident, technician
        )
        test_session.commit()
        assert test_session.query(NotificationOutbox).count() == 2

        client = TestClient(app)
        first = client.patch(
            f"/api/v1/work-orders/{work_orders[0].id}",
            json={"status": "completed", "diagnosis": "Replaced the lamp."},
        )
        assert first.status_code == 200, first.text
        test_session.refresh(incident)
        assert incident.status == "in_progress"
        assert test_session.query(NotificationOutbox).count() == 2

        second = client.patch(
            f"/api/v1/work-orders/{work_orders[1].id}",
            json={"status": "completed", "diagnosis": "Verified the repair."},
        )
        assert second.status_code == 200, second.text
        test_session.refresh(incident)
        assert incident.status == "resolved"

        queued = test_session.query(NotificationOutbox).all()
        assert len(queued) == 3
        resolution_email = next(
            item for item in queued if item.subject.endswith("resolved")
        )
        assert resolution_email.recipient_email == reporter.email
        assert resolution_email.status == "queued"
        assert resolution_email.event_type == "incident_resolved"
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        test_session.close()
        engine.dispose()


def test_correlated_report_emails_reporter_and_facilities_admin():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(bind=engine, autoflush=False)()

    reporter = User(
        email="reporter@example.com",
        hashed_password="!",
        name="Reporter",
        role="student",
    )
    admin = User(
        email="facilities@example.com",
        hashed_password="!",
        name="Facilities",
        role="admin",
        sub_role="facilities_admin",
    )
    building = Building(name="Test Building", code="TEST", total_floors=1)
    test_session.add_all([reporter, admin, building])
    test_session.flush()
    incident = Incident(
        incident_code="INC-TEST-0001",
        title="Broken light",
        description="A light is broken.",
        category="electrical",
        severity="medium",
        priority="P3",
        building_id=building.id,
        status="in_progress",
    )
    test_session.add(incident)
    test_session.flush()
    report = Report(
        report_code="RPT-TEST-0002",
        title="Another broken light",
        description="The same issue is present.",
        category="electrical",
        urgency="medium",
        building_id=building.id,
        reporter_id=reporter.id,
        reporter_role="student",
        source="web_portal",
        status="correlated",
        incident_id=incident.id,
    )
    test_session.add(report)
    test_session.flush()

    try:
        workflow_notifications.report_submitted(test_session, report)
        test_session.commit()
        queued = test_session.query(NotificationOutbox).all()
        assert {item.recipient_email for item in queued} == {
            reporter.email,
            admin.email,
        }
        admin_email = next(
            item for item in queued if item.recipient_email == admin.email
        )
        assert incident.incident_code in admin_email.subject
        assert incident.incident_code in admin_email.body
    finally:
        test_session.close()
        engine.dispose()


def test_legacy_queued_email_is_cancelled_without_delivery(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(bind=engine, autoflush=False)()
    legacy_email = NotificationOutbox(
        recipient_email="unexpected@example.com",
        channel="email",
        subject="Old unrelated notification",
        body="This was queued by the previous workflow.",
        status="queued",
        attempts=0,
    )
    test_session.add(legacy_email)
    test_session.commit()

    def unexpected_delivery(*args, **kwargs):
        pytest.fail("Legacy email must not be delivered.")

    monkeypatch.setattr(
        "app.services.notification_service.gmail_sender.send",
        unexpected_delivery,
    )

    try:
        notification_service.process_pending_outbox(test_session)
        test_session.refresh(legacy_email)
        assert legacy_email.status == "cancelled"
        assert legacy_email.attempts == 0
    finally:
        test_session.close()
        engine.dispose()


def test_simulated_email_is_not_reported_as_sent(monkeypatch):
    from app.integrations.gmail_sender import DeliveryResult

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(bind=engine, autoflush=False)()
    outbox_email = NotificationOutbox(
        recipient_email="reporter@example.com",
        channel="email",
        event_type="report_submitted",
        subject="Report received",
        body="Your report was received.",
        status="queued",
        attempts=0,
    )
    test_session.add(outbox_email)
    test_session.commit()
    monkeypatch.setattr(
        "app.services.notification_service.gmail_sender.send",
        lambda **kwargs: DeliveryResult(
            delivered=True,
            simulated=True,
            mode="simulated",
        ),
    )

    try:
        result = notification_service.process_pending_outbox(test_session)
        test_session.refresh(outbox_email)
        assert result["sent"] == 0
        assert result["simulated"] == 1
        assert result["delivery_mode"] == "simulated"
        assert outbox_email.status == "simulated"
    finally:
        test_session.close()
        engine.dispose()
