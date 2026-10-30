from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.database.models.asset import Asset
from app.services.predictive_maintenance_service import predictive_maintenance_service

client = TestClient(app)

def test_predictive_fleet_overview_endpoint():
    res = client.get("/api/v1/assets/predictive-overview")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "total_assets" in data["summary"]
    assert "high_risk_assets" in data
    assert "attention_required_assets" in data
    assert "healthy_assets" in data
    assert "upcoming_schedules" in data

def test_single_asset_health_scoring():
    db = SessionLocal()
    try:
        asset = db.query(Asset).first()
        assert asset is not None

        evaluation = predictive_maintenance_service.evaluate_asset_health(db, asset)
        assert "health_score" in evaluation
        assert 0 <= evaluation["health_score"] <= 100
        assert evaluation["risk_level"] in ["Healthy", "Attention Required", "High Risk"]
        assert 0.0 <= evaluation["failure_probability_30d"] <= 1.0
        assert "recommended_action" in evaluation
        assert "score_breakdown" in evaluation

        res = client.get(f"/api/v1/assets/{asset.id}/predictive-health")
        assert res.status_code == 200
        api_data = res.json()
        assert api_data["asset_id"] == asset.id
        assert api_data["health_score"] == evaluation["health_score"]
    finally:
        db.close()

