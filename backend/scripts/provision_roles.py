"""
CampusOps - provision the real demo accounts and retire the seeded mock people.

Works against whatever ``DATABASE_URL`` points at, so it can be run either on
the local SQLite file or against Supabase Postgres:

    python scripts/provision_roles.py                       # local SQLite
    python scripts/provision_roles.py --target "postgresql://..." --password "..."

What it does (idempotent, safe to re-run):

1. Creates any missing tables (including ``role_assignments``) and adds the
   OAuth columns to an existing ``users`` table.
2. Upserts the four real demo accounts, one per role, and records them in
   ``role_assignments`` so Google sign-in can grant the right role server-side.
3. Gives the technician a staff profile so auto-dispatch can consider them.
4. Soft-deactivates every seeded @campusops.edu student/faculty/admin (and,
   unless --keep-seeded-technicians is passed, the seeded technicians).

Soft-deactivation never deletes rows, so reports, incidents, work orders,
bookings, notifications and audit history stay fully intact.
"""

import argparse
import json
import os
import sys
from datetime import datetime

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database.base import Base  # noqa: E402
import app.database.models as models  # noqa: E402

# The emails supplied for the demo. Role is granted from this table only.
DEMO_ACCOUNTS = [
    {
        "email": "rajesekersudharsan@gmail.com",
        "name": "Rajesekar Sudharsan",
        "role": "admin",
        "sub_role": "system_admin",
        "department": "Campus Operations",
    },
    {
        "email": "192573020.simats@saveetha.com",
        "name": "Simats Student",
        "role": "student",
        "sub_role": None,
        "department": None,
    },
    {
        "email": "susen469@gmail.com",
        "name": "Susen Faculty",
        "role": "faculty",
        "sub_role": None,
        "department": "Academics",
    },
    {
        "email": "techtroveversion3@gmail.com",
        "name": "Tech Trove",
        "role": "technician",
        "sub_role": "maintenance_technician",
        "department": "Facilities",
    },
]

TECH_SKILLS = ["network", "hardware", "electrical", "exam_setup", "hvac"]

# Columns added to an existing `users` table (create_all never alters tables).
NEW_USER_COLUMNS = {
    "auth_provider": "VARCHAR(20) DEFAULT 'password'",
    "provider_subject": "VARCHAR(255)",
    "email_verified": "BOOLEAN DEFAULT FALSE",
    "last_login_at": "TIMESTAMP",
}


def normalize_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def resolve_target(args) -> str:
    if args.target:
        return normalize_url(args.target)
    if args.password:
        ref = "pcmjjphqnjrebauyerdy"
        return (
            f"postgresql+psycopg2://postgres.{ref}:{args.password}"
            f"@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
        )
    return normalize_url(settings.DATABASE_URL)


def ensure_user_columns(engine) -> list:
    """Add the OAuth columns to a pre-existing users table."""
    added = []
    insp = inspect(engine)
    if "users" not in insp.get_table_names():
        return added
    existing = {c["name"] for c in insp.get_columns("users")}
    dialect = engine.dialect.name
    with engine.begin() as conn:
        for column, ddl in NEW_USER_COLUMNS.items():
            if column in existing:
                continue
            if dialect == "postgresql":
                conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column} {ddl}"))
            else:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {column} {ddl}"))
            added.append(column)
    return added


def upsert_accounts(db, password: str) -> None:
    created, updated = [], []

    for spec in DEMO_ACCOUNTS:
        email = spec["email"].lower()

        assignment = (
            db.query(models.RoleAssignment)
            .filter(models.RoleAssignment.email == email)
            .first()
        )
        if not assignment:
            assignment = models.RoleAssignment(email=email, created_at=datetime.utcnow())
            db.add(assignment)
        assignment.role = spec["role"]
        assignment.sub_role = spec["sub_role"]
        assignment.department = spec["department"]
        assignment.is_active = True

        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            user = models.User(
                email=email,
                hashed_password=hash_password(password),
                created_at=datetime.utcnow(),
            )
            db.add(user)
            created.append(email)
        else:
            updated.append(email)

        user.name = spec["name"]
        user.role = spec["role"]
        user.sub_role = spec["sub_role"]
        user.department = spec["department"]
        user.is_active = True
        user.email_verified = True
        user.auth_provider = user.auth_provider or "password"
        assignment.consumed_at = datetime.utcnow()

        db.flush()

        if spec["role"] == "technician":
            profile = (
                db.query(models.StaffProfile)
                .filter(models.StaffProfile.user_id == user.id)
                .first()
            )
            if not profile:
                profile = models.StaffProfile(user_id=user.id, created_at=datetime.utcnow())
                db.add(profile)
            profile.skills = json.dumps(TECH_SKILLS)
            profile.shift = profile.shift or "morning"
            profile.availability_status = profile.availability_status or "available"
            profile.current_workload = profile.current_workload or 0

    db.commit()
    print(f"  created users: {', '.join(created) if created else 'none'}")
    print(f"  updated users: {', '.join(updated) if updated else 'none'}")


def deactivate_mock_people(db, keep_technicians: bool) -> dict:
    keep_emails = {a["email"].lower() for a in DEMO_ACCOUNTS}
    roles = ["student", "faculty", "admin"]
    if not keep_technicians:
        roles.append("technician")

    demo_domain = models.User.email.ilike("%@campusops.edu")
    targets = (
        db.query(models.User)
        .filter(demo_domain, models.User.role.in_(roles), models.User.is_active.is_(True))
        .all()
    )

    counts = {}
    for user in targets:
        if user.email.lower() in keep_emails:
            continue
        user.is_active = False
        counts[user.role] = counts.get(user.role, 0) + 1
    db.commit()
    return counts


def verify(db) -> None:
    print("\n  active accounts by role:")
    for role, count in (
        db.query(models.User.role, models.User)
        .with_entities(models.User.role, text("count(*)"))
        .filter(models.User.is_active.is_(True))
        .group_by(models.User.role)
        .all()
    ):
        print(f"    {role:<12} {count}")

    print("\n  event data (must be untouched):")
    for model, label in (
        (models.Report, "reports"),
        (models.Incident, "incidents"),
        (models.WorkOrder, "work_orders"),
        (models.RoomBooking, "room_bookings"),
        (models.Notification, "notifications"),
        (models.AuditLog, "audit_logs"),
    ):
        print(f"    {label:<15} {db.query(model).count()}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision demo RBAC accounts.")
    parser.add_argument("--target", default=None, help="PostgreSQL/SQLite URL (defaults to DATABASE_URL)")
    parser.add_argument("--password", default=None, help="Supabase database password shortcut")
    parser.add_argument("--account-password", default="password123", help="Password for the four demo accounts")
    parser.add_argument(
        "--keep-seeded-technicians",
        action="store_true",
        help="Leave the 24 seeded @campusops.edu technicians active (auto-dispatch talent pool)",
    )
    parser.add_argument("--skip-deactivate", action="store_true", help="Only provision accounts, keep all mock people")
    args = parser.parse_args()

    url = resolve_target(args)
    is_sqlite = url.startswith("sqlite")
    print(f"Target: {'SQLite (local)' if is_sqlite else url.split('@')[-1]}")

    engine = create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False} if is_sqlite else {},
    )
    Base.metadata.create_all(bind=engine)

    added = ensure_user_columns(engine)
    if added:
        print(f"  added users columns: {', '.join(added)}")

    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        print("\n[1/3] Provisioning the four demo accounts")
        upsert_accounts(db, args.account_password)

        if args.skip_deactivate:
            print("\n[2/3] Skipping deactivation (--skip-deactivate)")
        else:
            print("\n[2/3] Soft-deactivating seeded mock people")
            counts = deactivate_mock_people(db, args.keep_seeded_technicians)
            print(f"  deactivated: {counts or 'nothing to do'}")

        print("\n[3/3] Verification")
        verify(db)
    finally:
        db.close()

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
