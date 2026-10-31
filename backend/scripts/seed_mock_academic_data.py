"""Seed idempotent faculty and technician mock data into the configured DB.

Run without flags to preview counts. Pass ``--apply`` to insert rows.
Mock users are not added to Google sign-in role assignments. Mock technicians
are marked on leave so real intake auto-dispatch never assigns production work
to demo accounts.
"""

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings  # noqa: E402
from app.database.models.booking import RoomBooking  # noqa: E402
from app.database.models.report import Report  # noqa: E402
from app.database.models.room import Room  # noqa: E402
from app.database.models.staff import StaffProfile  # noqa: E402
from app.database.models.user import User  # noqa: E402

FACULTY_COUNT = 20
TECHNICIAN_COUNT = 30

COURSES = [
    "Foundations of Computing",
    "Applied Mathematics",
    "Engineering Physics",
    "Database Systems",
    "Network Fundamentals",
    "Technical Communication",
    "Data Structures",
    "Electrical Circuits",
    "Environmental Science",
    "Computer Architecture",
    "Statistics for Engineering",
    "Human-Computer Interaction",
    "Operating Systems",
    "Digital Electronics",
    "Research Methods",
    "Artificial Intelligence",
    "Signals and Systems",
    "Materials Science",
    "Software Engineering",
    "Cybersecurity Essentials",
]

FACULTY_DEPARTMENTS = [
    "Computer Science",
    "Electrical Engineering",
    "Mathematics",
    "Physics",
    "Mechanical Engineering",
]

TECHNICIAN_SKILLS = [
    ["network", "wifi", "cabling", "router_config"],
    ["electrical", "power_distribution"],
    ["hardware", "av_equipment", "classroom_readiness"],
    ["hvac"],
    ["plumbing", "water_systems", "sanitary_maintenance"],
    ["general_cleaning", "sanitation", "waste_management"],
    ["exam_setup", "classroom_readiness", "av_equipment"],
]

TECHNICIAN_SUB_ROLES = [
    "maintenance_technician",
    "all_skills_technician",
    "janitor",
    "room_incharge",
    "floor_incharge",
]

REPORT_ISSUES = [
    ("network", "Wireless access point needs inspection"),
    ("electrical", "Classroom power outlet is not working"),
    ("classroom", "Projector needs a connectivity check"),
    ("equipment", "Teaching equipment needs routine inspection"),
    ("hvac", "Room temperature control needs inspection"),
]


def _mock_email(role: str, index: int) -> str:
    return f"mock.{role}.{index:03d}@example.invalid"


def _code(prefix: str, index: int) -> str:
    return f"{prefix}-MOCK-{index:04d}"


def _available_rooms(db: Session) -> List[Room]:
    return (
        db.query(Room)
        .filter(Room.status == "available")
        .order_by(Room.building_id, Room.room_number)
        .all()
    )


def _existing_counts(db: Session) -> Dict[str, int]:
    faculty_emails = [_mock_email("faculty", i) for i in range(1, FACULTY_COUNT + 1)]
    technician_emails = [
        _mock_email("technician", i) for i in range(1, TECHNICIAN_COUNT + 1)
    ]
    existing_users = (
        db.query(User.email)
        .filter(User.email.in_(faculty_emails + technician_emails))
        .all()
    )
    existing_user_emails = {row[0] for row in existing_users}
    existing_bookings = (
        db.query(RoomBooking.booking_code)
        .filter(
            RoomBooking.booking_code.in_(
                [_code("BKG", i) for i in range(1, FACULTY_COUNT * 3 + 1)]
            )
        )
        .count()
    )
    existing_reports = (
        db.query(Report.report_code)
        .filter(
            Report.report_code.in_(
                [_code("RPT", i) for i in range(1, FACULTY_COUNT + 1)]
            )
        )
        .count()
    )
    return {
        "users_to_add": FACULTY_COUNT + TECHNICIAN_COUNT - len(existing_user_emails),
        "bookings_to_add": FACULTY_COUNT * 3 - existing_bookings,
        "reports_to_add": FACULTY_COUNT - existing_reports,
    }


def seed_mock_data(db: Session) -> Dict[str, int]:
    rooms = _available_rooms(db)
    if not rooms:
        raise RuntimeError("No available rooms exist; cannot seed faculty schedules.")

    rooms_by_type = {
        room_type: [room for room in rooms if room.type == room_type]
        for room_type in ("classroom", "lab", "exam_hall")
    }
    if not all(rooms_by_type.values()):
        raise RuntimeError(
            "Available classroom, lab, and exam_hall rooms are all required."
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0)
    faculty_users: List[User] = []
    technician_users: List[User] = []
    created_users = 0
    created_profiles = 0
    created_bookings = 0
    created_reports = 0

    def get_or_create_user(
        email: str,
        *,
        name: str,
        role: str,
        sub_role: str = None,
        department: str,
        building_id: str = None,
    ) -> User:
        nonlocal created_users
        user = db.query(User).filter(User.email == email).first()
        if user:
            if user.role != role or user.auth_provider != "mock":
                raise RuntimeError(
                    f"Reserved mock email {email} already belongs to a non-mock account."
                )
            return user

        user = User(
            email=email,
            hashed_password="!",
            name=name,
            role=role,
            sub_role=sub_role,
            department=department,
            building_id=building_id,
            auth_provider="mock",
            email_verified=False,
            is_active=True,
        )
        db.add(user)
        db.flush()
        created_users += 1
        return user

    for index in range(1, FACULTY_COUNT + 1):
        room = rooms[index % len(rooms)]
        faculty_users.append(
            get_or_create_user(
                _mock_email("faculty", index),
                name=f"Mock Faculty {index:02d}",
                role="faculty",
                department=FACULTY_DEPARTMENTS[(index - 1) % len(FACULTY_DEPARTMENTS)],
                building_id=room.building_id,
            )
        )

    for index in range(1, TECHNICIAN_COUNT + 1):
        room = rooms[(index + FACULTY_COUNT) % len(rooms)]
        technician = get_or_create_user(
            _mock_email("technician", index),
            name=f"Mock Technician {index:02d}",
            role="technician",
            sub_role=TECHNICIAN_SUB_ROLES[(index - 1) % len(TECHNICIAN_SUB_ROLES)],
            department="Facilities",
            building_id=room.building_id,
        )
        technician_users.append(technician)

        profile = (
            db.query(StaffProfile)
            .filter(StaffProfile.user_id == technician.id)
            .first()
        )
        if not profile:
            db.add(
                StaffProfile(
                    user_id=technician.id,
                    skills=json.dumps(
                        TECHNICIAN_SKILLS[(index - 1) % len(TECHNICIAN_SKILLS)]
                    ),
                    shift=("morning", "evening", "night")[(index - 1) % 3],
                    assigned_building_id=room.building_id,
                    availability_status="on_leave",
                    current_workload=0,
                )
            )
            created_profiles += 1

    db.flush()

    purpose_specs = [
        ("lecture", "classroom", 10, 9, "Lecture"),
        ("lab_session", "lab", 11, 12, "Lab"),
        ("examination", "exam_hall", 13, 14, "Examination"),
    ]
    for faculty_index, faculty in enumerate(faculty_users):
        course = COURSES[faculty_index]
        for slot_index, (purpose, room_type, first_day, start_hour, label) in enumerate(
            purpose_specs
        ):
            booking_index = faculty_index * 3 + slot_index + 1
            booking_code = _code("BKG", booking_index)
            existing = (
                db.query(RoomBooking)
                .filter(RoomBooking.booking_code == booking_code)
                .first()
            )
            if existing:
                continue

            room_list = rooms_by_type[room_type]
            room = room_list[faculty_index % len(room_list)]
            day_offset = first_day + faculty_index // len(room_list)
            start_time = (now + timedelta(days=day_offset)).replace(
                hour=start_hour + (faculty_index % 2) * 2
            )
            db.add(
                RoomBooking(
                    booking_code=booking_code,
                    room_id=room.id,
                    user_id=faculty.id,
                    user_role="faculty",
                    title=f"MOCK - {course} {label}",
                    purpose=purpose,
                    start_time=start_time,
                    end_time=start_time + timedelta(hours=2),
                    status="confirmed",
                    equipment_required=json.dumps(
                        ["projector", "wifi"]
                        if purpose != "examination"
                        else ["wifi", "exam_seating"]
                    ),
                )
            )
            created_bookings += 1

        report_code = _code("RPT", faculty_index + 1)
        existing_report = (
            db.query(Report).filter(Report.report_code == report_code).first()
        )
        if not existing_report:
            category, title = REPORT_ISSUES[faculty_index % len(REPORT_ISSUES)]
            room = rooms[faculty_index % len(rooms)]
            db.add(
                Report(
                    report_code=report_code,
                    title=f"MOCK - {title}",
                    description=(
                        "Demo-only faculty facilities report for workspace preview."
                    ),
                    category=category,
                    urgency=("low", "medium", "high")[
                        faculty_index % 3
                    ],
                    building_id=room.building_id,
                    room_id=room.id,
                    reporter_id=faculty.id,
                    reporter_role="faculty",
                    source="mock_seed",
                    status="submitted",
                    ai_extracted_meta="{}",
                )
            )
            created_reports += 1

    db.flush()
    return {
        "created_users": created_users,
        "created_staff_profiles": created_profiles,
        "created_bookings": created_bookings,
        "created_reports": created_reports,
        "faculty_accounts": len(faculty_users),
        "technician_accounts": len(technician_users),
    }


def _engine_url() -> str:
    url = settings.DATABASE_URL
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Insert the mock rows. Without this flag the script only previews counts.",
    )
    args = parser.parse_args()

    url = _engine_url()
    connect_args = {"connect_timeout": 10} if url.startswith("postgresql+") else {}
    engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
    if not inspect(engine).has_table("reports", schema="public" if engine.dialect.name == "postgresql" else None):
        raise RuntimeError("The configured database has no reports table.")

    SessionLocal = sessionmaker(bind=engine, autoflush=False)
    db = SessionLocal()
    try:
        counts = _existing_counts(db)
        if not args.apply:
            print("Dry run only; no rows were changed.")
            for key, value in counts.items():
                print(f"{key}: {value}")
            print("Planned staff profiles: up to 30")
            print("Mock accounts will not be added to Google sign-in allowlists.")
            print("Mock technicians are marked on_leave to avoid real auto-dispatch.")
            return

        results = seed_mock_data(db)
        db.commit()
        print("Mock data committed successfully.")
        for key, value in results.items():
            print(f"{key}: {value}")
        print("No Google sign-in assignments or email outbox rows were created.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    main()
