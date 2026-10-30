"""
CampusOps — SQLite to Supabase PostgreSQL Migration Script
Usage:
  python scripts/migrate_to_supabase.py --target "postgresql://postgres.pcmjjphqnjrebauyerdy:[PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"

Or if running interactively:
  python scripts/migrate_to_supabase.py --password "YOUR_DB_PASSWORD"
"""

import os
import sys
import re
import argparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.base import Base
from app.config import settings, SQLITE_URL
import app.database.models as models

ORDERED_MODELS = [
    models.User,
    models.Building,
    models.Floor,
    models.Room,
    models.Asset,
    models.StaffProfile,
    models.InventoryItem,
    models.Incident,
    models.Report,
    models.WorkOrder,
    models.StockReservation,
    models.RoomBooking,
    models.ApprovalRequest,
    models.ProcurementRequest,
    models.Notification,
    models.NotificationOutbox,
    models.AuditLog,
    models.HistoricalResolution,
    models.PredictiveAlert,
]

def sanitize_and_resolve_url(target_url: str) -> str:
    # Check for un-substituted placeholders
    for placeholder in ["[PROJECT-REF]", "[YOUR-PROJECT-REF]", "[PASSWORD]", "[YOUR-DB-PASSWORD]", "[YOUR-PASSWORD]"]:
        if placeholder in target_url:
            raise ValueError(
                f"Connection string contains placeholder '{placeholder}'. "
                "Please replace it with your actual Supabase project reference or database password."
            )

    # Normalize postgres url for SQLAlchemy
    if target_url.startswith("postgres://"):
        target_url = target_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif target_url.startswith("postgresql://") and "+psycopg2" not in target_url:
        target_url = target_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    # Note: On IPv4 networks, direct db.<ref>.supabase.co fails DNS because Supabase direct hosts are IPv6-only.
    # Automatically convert db.<ref>.supabase.co to pooler host if ap-south-1
    direct_match = re.search(r"postgresql\+psycopg2://postgres:(.*?)@db\.([a-z0-9]+)\.supabase\.co:5432/(.*)", target_url)
    if direct_match:
        pw, ref, dbname = direct_match.groups()
        print("💡 Tip: Direct db.*.supabase.co uses IPv6. Switching to IPv4 Supabase Connection Pooler...")
        target_url = f"postgresql+psycopg2://postgres.{ref}:{pw}@aws-0-ap-south-1.pooler.supabase.com:5432/{dbname}"

    return target_url

def migrate(target_url: str):
    target_url = sanitize_and_resolve_url(target_url)

    print(f"\n[1/3] Connecting to source SQLite: {SQLITE_URL}")
    source_engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
    SourceSession = sessionmaker(bind=source_engine)
    source_db = SourceSession()

    print(f"[2/3] Connecting to target Supabase PostgreSQL...")
    target_engine = create_engine(target_url, pool_pre_ping=True)
    TargetSession = sessionmaker(bind=target_engine)
    target_db = TargetSession()

    print("      Creating tables on Supabase PostgreSQL (DDL)...")
    Base.metadata.create_all(bind=target_engine)
    print("      Tables ready.")

    print("\n[3/3] Migrating entities from SQLite into Supabase...")
    total_migrated = 0

    for model in ORDERED_MODELS:
        table_name = model.__tablename__
        records = source_db.query(model).all()
        count = len(records)
        if count == 0:
            print(f"  - {table_name}: 0 records (skipped)")
            continue

        for r in records:
            data = {col.name: getattr(r, col.name) for col in model.__table__.columns}
            target_instance = model(**data)
            target_db.merge(target_instance)

        target_db.commit()
        print(f"  ✓ {table_name}: {count} records synced")
        total_migrated += count

    source_db.close()
    target_db.close()
    print(f"\n🎉 Migration complete! Successfully synced {total_migrated} records into Supabase PostgreSQL.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate CampusOps database from SQLite to Supabase PostgreSQL.")
    parser.add_argument(
        "--target",
        default=None,
        help="Supabase PostgreSQL connection URL"
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Supabase database password (if not embedded in --target)"
    )
    args = parser.parse_args()

    target_url = args.target

    # If target not provided via CLI, check env
    if not target_url:
        env_url = os.getenv("DATABASE_URL")
        if env_url and "sqlite" not in env_url:
            target_url = env_url

    # If still not provided, construct from known project ref and password
    if not target_url and args.password:
        project_ref = "pcmjjphqnjrebauyerdy"
        target_url = f"postgresql://postgres.{project_ref}:{args.password}@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"

    if not target_url or "sqlite" in target_url:
        print("ERROR: A valid PostgreSQL connection string or --password is required.")
        print("\nUsage:")
        print("  python scripts/migrate_to_supabase.py --password \"YOUR_SUPABASE_DB_PASSWORD\"")
        print("OR:")
        print("  python scripts/migrate_to_supabase.py --target \"postgresql://postgres.pcmjjphqnjrebauyerdy:YOUR_PASSWORD@aws-0-ap-south-1.pooler.supabase.com:5432/postgres\"\n")
        sys.exit(1)

    try:
        migrate(target_url)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
