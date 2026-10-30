from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.database.models.user import User
from app.database.models.recovery import RecoveryExecution
from app.services.recovery_execution_service import recovery_execution_service
from app.services.recovery_verification_service import recovery_verification_service

client = TestClient(app)

def test_recovery_lifecycle_execution_and_verification():
    db = SessionLocal()
    try:
        # Find facilities admin or system admin
        admin_user = db.query(User).filter(User.role == "admin", User.sub_role == "system_admin").first()
        assert admin_user is not None

        # 1. Initiate Recovery Plan
        execution = recovery_execution_service.initiate_recovery(
            db=db,
            incident_id=None,
            disruption_type="test_disruption",
            chosen_plan_id="plan_alpha",
            actions_spec=[
                {
                    "action_type": "notification_broadcast",
                    "target_entity_type": "user",
                    "target_entity_id": admin_user.id,
                    "payload": {
                        "recipients": [admin_user.id],
                        "title": "Test Recovery Notice",
                        "message": "Testing automated recovery dispatch"
                    }
                }
            ],
            initiated_by_user=admin_user
        )
        assert execution.id is not None
        assert execution.status == "in_progress"

        # 2. Execute Staged Actions
        exec_res = recovery_execution_service.execute_recovery_actions(
            db=db,
            execution_id=execution.id,
            operator=admin_user
        )
        assert exec_res["status"] == "awaiting_verification"
        assert len(exec_res["actions_executed"]) == 1
        assert exec_res["actions_executed"][0]["status"] == "completed"

        # 3. Independent Verification
        verify_res = recovery_verification_service.verify_recovery_execution(
            db=db,
            execution_id=execution.id,
            inspector_user=admin_user
        )
        assert "verification_status" in verify_res
        assert verify_res["execution_id"] == execution.id
        assert verify_res["is_success"] is True

        # 4. Query via API
        list_res = client.get("/api/v1/recovery/executions?limit=5")
        assert list_res.status_code == 200
        executions_list = list_res.json()
        assert any(e["id"] == execution.id for e in executions_list)

    finally:
        db.close()

