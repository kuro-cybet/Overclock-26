"""
CampusOps - migrate the local SQLite database into Supabase Postgres.

    python scripts/migrate_to_supabase.py --password "YOUR_SUPABASE_DB_PASSWORD"
    python scripts/migrate_to_supabase.py --target "postgresql://...:6543/postgres"

The script:
  1. reads every table from the local SQLite database,
  2. creates all 32 tables on the target via SQLAlchemy metadata (so nothing is
     missing even if the Supabase schema was only partially created),
  3. inserts rows in dependency order with ON CONFLICT DO NOTHING, so re-running
     it is safe and never duplicates or overwrites edited rows,
  4. verifies row counts per table and reports any mismatch.

It is read-only with respect to the SQLite source.
"""

import argparse
import os
import sys

from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import SQLITE_URL  # noqa: E402
from app.database.base import Base  # noqa: E402
import app.database.models  # noqa: F401,E402  (registers every table on Base.metadata)

CHUNK = 500
SUPABASE_PROJECT_REF = "pcmjjphqnjrebauyerdy"
SUPABASE_POOLER = f"aws-0-ap-south-1.pooler.supabase.com"


def normalize_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def resolve_target(args) -> str:
    if args.target:
        for placeholder in ("[PASSWORD]", "[YOUR-PASSWORD]", "[YOUR-DB-PASSWORD]", "[PROJECT-REF]"):
            if placeholder in args.target:
                raise ValueError(f"Connection string still contains {placeholder}.")
        return normalize_url(args.target)
    if args.password:
        return (
            f"postgresql+psycopg2://postgres.{SUPABASE_PROJECT_REF}:{args.password}"
            f"@{SUPABASE_POOLER}:5432/postgres"
        )
    raise ValueError("Provide --password or --target.")


def lockdown(target_engine, table_names) -> None:
    """Close direct PostgREST access with the public anon key.

    The API talks to Postgres as the database owner, which bypasses RLS, so the
    app keeps working while ``anon``/``authenticated`` get no table access at
    all. The Gmail Edge Function uses the service role and is unaffected.
    """
    with target_engine.begin() as conn:
        for name in table_names:
            safe = name.replace('"', "")
            conn.exec_driver_sql(
                f'ALTER TABLE public."{safe}" ENABLE ROW LEVEL SECURITY'
            )
        conn.exec_driver_sql(
            "REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated"
        )
        conn.exec_driver_sql(
            "REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated"
        )
    print(f"      RLS enabled on {len(table_names)} tables; anon/authenticated revoked")


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy the CampusOps SQLite data into Supabase Postgres.")
    parser.add_argument("--target", default=None, help="Target PostgreSQL connection URL")
    parser.add_argument("--password", default=None, help="Supabase database password shortcut")
    parser.add_argument("--source", default=None, help="Source SQLite URL (defaults to the tracked local DB)")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="DROP and recreate the public schema on the target first (destroys existing target data)",
    )
    parser.add_argument(
        "--no-lockdown",
        action="store_true",
        help="Do not enable RLS / revoke anon access after loading",
    )
    args = parser.parse_args()

    try:
        target_url = resolve_target(args)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    source_url = args.source or SQLITE_URL
    print(f"\n[1/4] Source      : {source_url}")
    print(f"[2/4] Destination : {target_url.split('@')[-1]}")

    source = create_engine(
        source_url,
        connect_args={"check_same_thread": False} if source_url.startswith("sqlite") else {},
    )
    target = create_engine(target_url, pool_pre_ping=True, pool_size=3, max_overflow=2)

    with target.begin() as conn:
        conn.exec_driver_sql("select 1")
    print("      connection OK")

    tables = list(Base.metadata.sorted_tables)
    print(f"\n[3/4] Creating/filling {len(tables)} tables")

    if args.recreate:
        print("      --recreate: dropping existing CampusOps tables")
        existing = set(inspect(target).get_table_names(schema="public"))
        with target.begin() as conn:
            # Reverse dependency order so children are removed before parents.
            for table in reversed(tables):
                if table.name in existing:
                    safe = table.name.replace('"', "")
                    conn.exec_driver_sql(
                        f'DROP TABLE IF EXISTS public."{safe}" CASCADE'
                    )

    Base.metadata.create_all(bind=target)

    total = 0
    failures = []
    with source.connect() as src, target.begin() as dst:
        for table in tables:
            rows = [dict(r._mapping) for r in src.execute(select(table))]
            if not rows:
                print(f"      {table.name:<34} 0 (skipped)")
                continue
            try:
                for i in range(0, len(rows), CHUNK):
                    chunk = rows[i : i + CHUNK]
                    stmt = pg_insert(table).values(chunk).on_conflict_do_nothing()
                    dst.execute(stmt)
                total += len(rows)
                print(f"      {table.name:<34} {len(rows)}")
            except Exception as exc:  # noqa: BLE001
                failures.append((table.name, str(exc)[:180]))
                print(f"      {table.name:<34} FAILED -> {str(exc)[:120]}")

    print(f"\n[4/4] Verification ({total} source rows)")
    mismatches = []
    with source.connect() as src, target.connect() as dst:
        for table in tables:
            expected = src.execute(select(func.count()).select_from(table)).scalar_one()
            actual = dst.execute(select(func.count()).select_from(table)).scalar_one()
            if expected != actual:
                mismatches.append((table.name, expected, actual))
    if mismatches:
        print("      row-count mismatches (target may already hold extra rows):")
        for name, expected, actual in mismatches:
            print(f"        {name:<34} sqlite={expected:<6} postgres={actual}")
    else:
        print("      every table matches the source row count")

    if failures:
        print("\n      tables that failed to load:")
        for name, err in failures:
            print(f"        {name}: {err}")
        return 1

    if not args.no_lockdown:
        print("\n[+] Locking down direct Supabase access")
        actual_tables = inspect(target).get_table_names(schema="public")
        lockdown(target, actual_tables)

    print("\nMigration complete. Next: python scripts/provision_roles.py --password <same password>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
