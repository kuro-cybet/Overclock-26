from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.services.operational_intelligence_service import operational_intelligence_service

client = TestClient(app)

def test_operational_assessment_endpoint():
    res = client.get("/api/v1/intelligence/operational-assessment")
    assert res.status_code == 200
    data = res.json()
    assert "systemic_readiness_score" in data
    assert 0 <= data["systemic_readiness_score"] <= 100
    assert "summary_metrics" in data
    assert "findings" in data
    assert "building_clusters" in data["findings"]
    assert "rooms_at_risk" in data["findings"]
    assert "affected_examinations" in data["findings"]
    assert "overloaded_technicians" in data["findings"]
    assert "inventory_shortages" in data["findings"]
    assert "sla_projections" in data["findings"]
    assert "repeated_asset_failures" in data["findings"]

def test_building_clusters_endpoint():
    res = client.get("/api/v1/intelligence/building-clusters")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)

def test_decision_explanations_endpoint():
    res = client.get("/api/v1/intelligence/explanations?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if len(data) > 0:
        first = data[0]
        assert "decision_type" in first
        assert "chosen_option" in first
        assert "confidence_score" in first
        assert "explanation_text" in first

def test_service_direct_assessment():
    db = SessionLocal()
    try:
        assessment = operational_intelligence_service.get_full_operational_assessment(db)
        assert assessment["systemic_readiness_score"] >= 0
        assert "findings" in assessment
    finally:
        db.close()

