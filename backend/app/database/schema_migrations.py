"""Small, idempotent schema repairs for pre-existing SQLite databases.

The repository ships a tracked ``campusops.db`` that was created by an older
version of the models.  ``Base.metadata.create_all`` never alters existing
tables, so a few column definitions drifted from the current models.

SQLite schema repairs run only when drift is detected. The role-assignment
migration helper is also used by provisioning on PostgreSQL deployments.
"""

import logging

from sqlalchemy import Engine, text

logger = logging.getLogger(__name__)

# recovery_executions was originally created with incident_id/chosen_plan_id
# NOT NULL, while the model allows them to be empty (recovery can be initiated
# without a linked incident).  A partial repair also left recovery_actions
# pointing at a renamed table, so both are rebuilt together.
_RECOVERY_EXECUTIONS_DDL = """
CREATE TABLE recovery_executions_new (
    id VARCHAR(36) NOT NULL,
    incident_id VARCHAR(36),
    disruption_type VARCHAR(100) NOT NULL,
    chosen_plan_id VARCHAR(50),
    status VARCHAR(50) NOT NULL,
    executed_by_id VARCHAR(36),
    executed_at DATETIME,
    verification_status VARCHAR(50) NOT NULL,
    verification_outcome TEXT,
    verified_at DATETIME,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(incident_id) REFERENCES incidents (id) ON DELETE CASCADE,
    FOREIGN KEY(executed_by_id) REFERENCES users (id) ON DELETE SET NULL
)
"""

_RECOVERY_ACTIONS_DDL = """
CREATE TABLE recovery_actions_new (
    id VARCHAR(36) NOT NULL,
    execution_id VARCHAR(36) NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    target_entity_type VARCHAR(50) NOT NULL,
    target_entity_id VARCHAR(36) NOT NULL,
    status VARCHAR(50) NOT NULL,
    action_payload TEXT,
    result_payload TEXT,
    error_message TEXT,
    started_at DATETIME,
    completed_at DATETIME,
    PRIMARY KEY (id),
    FOREIGN KEY(execution_id) REFERENCES recovery_executions (id) ON DELETE CASCADE
)
"""


# Columns added to `users` for Google sign-in after the tracked SQLite file was
# created.  Kept in sync with app/database/models/user.py.
_USER_COLUMNS = {
    "auth_provider": "VARCHAR(20) DEFAULT 'password'",
    "provider_subject": "VARCHAR(255)",
    "email_verified": "BOOLEAN DEFAULT 0",
    "last_login_at": "DATETIME",
}

_ROLE_ASSIGNMENT_TABLES = {
    "admin": "admin_assignments",
    "technician": "technician_assignments",
    "faculty": "faculty_assignments",
    "student": "student_assignments",
}

_ROLE_ASSIGNMENT_COLUMNS = """
    id VARCHAR(36) NOT NULL,
    email VARCHAR(255) NOT NULL,
    sub_role VARCHAR(50),
    department VARCHAR(100),
    building_id VARCHAR(36),
    floor_id VARCHAR(36),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    invited_by VARCHAR(36),
    created_at TIMESTAMP NOT NULL,
    consumed_at TIMESTAMP,
    PRIMARY KEY (id)
"""


def _table_exists(conn, table: str) -> bool:
    row = conn.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def _repair_users_and_rbac(conn) -> None:
    """Add the OAuth columns and role-specific allowlist tables if missing."""
    if _table_exists(conn, "users"):
        existing = set(_columns(conn, "users"))
        for column, ddl in _USER_COLUMNS.items():
            if column not in existing:
                conn.exec_driver_sql(f"ALTER TABLE users ADD COLUMN {column} {ddl}")
                logger.info("[schema] added users.%s", column)
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_users_provider_subject "
            "ON users (provider_subject)"
        )

    _ensure_role_assignment_tables(conn)
    _migrate_legacy_role_assignments(conn)


def _ensure_role_assignment_tables(conn) -> None:
    for table in _ROLE_ASSIGNMENT_TABLES.values():
        conn.exec_driver_sql(
            f"CREATE TABLE IF NOT EXISTS {table} ({_ROLE_ASSIGNMENT_COLUMNS})"
        )
        conn.exec_driver_sql(
            f"CREATE UNIQUE INDEX IF NOT EXISTS ix_{table}_email ON {table} (email)"
        )
        logger.debug("[schema] ensured %s table", table)


def _migrate_legacy_role_assignments(conn) -> None:
    if not _table_exists(conn, "role_assignments"):
        return

    rows = conn.execute(text("SELECT * FROM role_assignments")).mappings().all()
    unsupported = sorted({row["role"] for row in rows} - _ROLE_ASSIGNMENT_TABLES.keys())
    if unsupported:
        raise ValueError(
            "Cannot migrate role_assignments with unsupported roles: "
            + ", ".join(unsupported)
        )

    columns = (
        "id",
        "email",
        "sub_role",
        "department",
        "building_id",
        "floor_id",
        "is_active",
        "invited_by",
        "created_at",
        "consumed_at",
    )
    values = ", ".join(f":{column}" for column in columns)
    updates = ", ".join(
        f"{column} = excluded.{column}" for column in columns if column != "id"
    )
    for row in rows:
        table = _ROLE_ASSIGNMENT_TABLES[row["role"]]
        conn.execute(
            text(
                f"INSERT INTO {table} ({', '.join(columns)}) "
                f"VALUES ({values}) "
                f"ON CONFLICT (email) DO UPDATE SET {updates}"
            ),
            {column: row[column] for column in columns},
        )

    conn.exec_driver_sql("DROP TABLE role_assignments")
    logger.info("[schema] migrated %s legacy role assignments", len(rows))


def migrate_role_assignments(engine: Engine) -> None:
    """Create the role allowlists and migrate the legacy table on any supported DB."""
    with engine.begin() as conn:
        _ensure_role_assignment_tables(conn)
        _migrate_legacy_role_assignments(conn)


def _columns(conn, table: str):
    rows = conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
    # PRAGMA table_info: cid, name, type, notnull, dflt_value, pk
    return {row[1]: row for row in rows}


def _foreign_keys(conn, table: str):
    rows = conn.exec_driver_sql(f"PRAGMA foreign_key_list({table})").fetchall()
    # PRAGMA foreign_key_list: id, seq, table, from, to, on_update, on_delete, match
    return rows


def _recovery_schema_needs_repair(conn) -> bool:
    columns = _columns(conn, "recovery_executions")
    if not columns:
        return False

    incident = columns.get("incident_id")
    chosen = columns.get("chosen_plan_id")
    drift = bool(incident and incident[3]) or bool(chosen and chosen[3])

    broken_fk = any(fk[2] != "recovery_executions" for fk in _foreign_keys(conn, "recovery_actions"))
    return drift or broken_fk


def _copy_rows(conn, source: str, target: str, columns) -> None:
    if not _columns(conn, source):
        return
    column_list = ", ".join(columns)
    conn.exec_driver_sql(
        f"INSERT INTO {target} ({column_list}) SELECT {column_list} FROM {source}"
    )


def _repair_recovery_schema(conn) -> None:
    if not _recovery_schema_needs_repair(conn):
        return

    logger.warning(
        "[schema] Rebuilding recovery tables to match the model "
        "(nullable incident_id/chosen_plan_id and a valid action foreign key)."
    )

    conn.exec_driver_sql("DROP TABLE IF EXISTS recovery_executions_new")
    conn.exec_driver_sql("DROP TABLE IF EXISTS recovery_actions_new")
    conn.exec_driver_sql("DROP TABLE IF EXISTS recovery_executions_old")

    conn.exec_driver_sql(_RECOVERY_EXECUTIONS_DDL)
    conn.exec_driver_sql(_RECOVERY_ACTIONS_DDL)

    _copy_rows(
        conn,
        "recovery_executions",
        "recovery_executions_new",
        (
            "id",
            "incident_id",
            "disruption_type",
            "chosen_plan_id",
            "status",
            "executed_by_id",
            "executed_at",
            "verification_status",
            "verification_outcome",
            "verified_at",
            "created_at",
        ),
    )
    _copy_rows(
        conn,
        "recovery_actions",
        "recovery_actions_new",
        (
            "id",
            "execution_id",
            "action_type",
            "target_entity_type",
            "target_entity_id",
            "status",
            "action_payload",
            "result_payload",
            "error_message",
            "started_at",
            "completed_at",
        ),
    )

    # Drop the child first so the parent is never referenced mid-migration.
    conn.exec_driver_sql("DROP TABLE IF EXISTS recovery_actions")
    conn.exec_driver_sql("DROP TABLE IF EXISTS recovery_executions")
    conn.exec_driver_sql("ALTER TABLE recovery_executions_new RENAME TO recovery_executions")
    conn.exec_driver_sql("ALTER TABLE recovery_actions_new RENAME TO recovery_actions")

    conn.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_recovery_executions_incident_id "
        "ON recovery_executions (incident_id)"
    )
    conn.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_recovery_executions_disruption_type "
        "ON recovery_executions (disruption_type)"
    )
    conn.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_recovery_actions_execution_id "
        "ON recovery_actions (execution_id)"
    )


def run_startup_migrations(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.begin() as conn:
            _repair_users_and_rbac(conn)
            _repair_recovery_schema(conn)
    except Exception:  # pragma: no cover - never block startup on a repair
        logger.exception("[schema] SQLite schema repair failed; continuing startup.")
