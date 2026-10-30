"""Small, idempotent schema repairs for pre-existing SQLite databases.

The repository ships a tracked ``campusops.db`` that was created by an older
version of the models.  ``Base.metadata.create_all`` never alters existing
tables, so a few column definitions drifted from the current models.

This module only runs for SQLite and only when it detects the drift, so it is
safe on fresh databases, Postgres deployments and repeated startups.
"""

import logging

from sqlalchemy import Engine

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
            _repair_recovery_schema(conn)
            rep_cols = _columns(conn, "reports")
            if rep_cols and "contact_phone" not in rep_cols:
                conn.exec_driver_sql("ALTER TABLE reports ADD COLUMN contact_phone VARCHAR(30)")
    except Exception:  # pragma: no cover - never block startup on a repair
        logger.exception("[schema] SQLite schema repair failed; continuing startup.")
