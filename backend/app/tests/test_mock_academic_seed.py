import app.database.models  # noqa: F401
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.models.booking import RoomBooking
from app.database.models.campus import Building
from app.database.models.notification import NotificationOutbox
from app.database.models.report import Report
from app.database.models.role_assignment import FacultyAssignment, TechnicianAssignment
from app.database.models.room import Room
from app.database.models.staff import StaffProfile
from app.database.models.user import User
from scripts.seed_mock_academic_data import seed_mock_data


def test_mock_academic_seed_is_idempotent_and_does_not_allow_login():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    building = Building(name="Mock Building", code="MOCK", total_floors=1)
    session.add(building)
    session.flush()
    for index, room_type in enumerate(("classroom", "lab", "exam_hall"), start=1):
        session.add(
            Room(
                building_id=building.id,
                floor_id=f"floor-{index}",
                room_number=f"{index:03d}",
                name=f"Mock {room_type}",
                type=room_type,
                capacity=40,
                status="available",
            )
        )
    session.commit()

    try:
        first = seed_mock_data(session)
        session.commit()
        second = seed_mock_data(session)
        session.commit()

        assert first == {
            "created_users": 50,
            "created_staff_profiles": 30,
            "created_bookings": 60,
            "created_reports": 20,
            "faculty_accounts": 20,
            "technician_accounts": 30,
        }
        assert second["created_users"] == 0
        assert second["created_staff_profiles"] == 0
        assert second["created_bookings"] == 0
        assert second["created_reports"] == 0
        assert session.query(User).count() == 50
        assert session.query(StaffProfile).count() == 30
        assert session.query(RoomBooking).count() == 60
        assert session.query(Report).count() == 20
        assert session.query(FacultyAssignment).count() == 0
        assert session.query(TechnicianAssignment).count() == 0
        assert session.query(NotificationOutbox).count() == 0
        assert {
            profile.availability_status
            for profile in session.query(StaffProfile).all()
        } == {"on_leave"}
    finally:
        session.close()
        engine.dispose()
