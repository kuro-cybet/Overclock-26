import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.database.schema_migrations import run_startup_migrations

db_url = settings.DATABASE_URL

# Normalize postgres URI for SQLAlchemy if using Supabase PostgreSQL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif db_url.startswith("postgresql://") and "+psycopg2" not in db_url and "+asyncpg" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

if "sqlite" in db_url:
    # Ensure local sqlite data directory exists
    clean_path = db_url.replace("sqlite:///", "")
    if clean_path and os.path.dirname(clean_path):
        os.makedirs(os.path.dirname(os.path.abspath(clean_path)), exist_ok=True)
    connect_args = {"check_same_thread": False}
    engine = create_engine(db_url, connect_args=connect_args)
else:
    # PostgreSQL / Supabase connection with pre-ping check
    engine = create_engine(db_url, pool_pre_ping=True, pool_size=10, max_overflow=20)

# Repair known drift between the tracked SQLite file and the current models.
run_startup_migrations(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
