from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.asset import Asset
from app.core.exceptions import EntityNotFoundError
from app.services.predictive_maintenance_service import predictive_maintenance_service
from app.schemas.asset import (
    AssetResponse,
    AssetPredictiveHealthResponse,
    FleetPredictiveOverviewResponse
)

router = APIRouter(prefix="/assets", tags=["assets"])

@router.get(
    "/predictive-overview",
    response_model=FleetPredictiveOverviewResponse,
    summary="Get Campus Fleet Predictive Overview",
    description="Fleet-wide predictive maintenance status: healthy, attention required, high risk assets, 30-day failure probabilities, and upcoming preventive maintenance schedules."
)
def get_predictive_fleet_overview(db: Session = Depends(get_db)):
    """
    Scans all campus physical assets and calculates failure probabilities and preventive schedules.
    """
    return predictive_maintenance_service.get_fleet_predictive_overview(db=db)

@router.get(
    "",
    response_model=List[AssetResponse],
    summary="List Campus Assets",
    description="Retrieves campus physical assets (HVAC, network switches, AV projectors, lab instruments) with optional filtering by category, building, or room."
)
def list_assets(
    category: Optional[str] = Query(None, description="Asset category: `network`, `av_equipment`, `hvac`, `electrical`, `furniture`, `lab_equipment`"),
    building_id: Optional[str] = Query(None, description="Campus building UUID"),
    room_id: Optional[str] = Query(None, description="Campus room UUID"),
    limit: int = Query(150, ge=1, le=500, description="Maximum assets to return"),
    db: Session = Depends(get_db)
):
    """
    List physical assets with serial numbers and inspection dates.
    """
    q = db.query(Asset)
    if category:
        q = q.filter(Asset.category == category)
    if building_id:
        q = q.filter(Asset.building_id == building_id)
    if room_id:
        q = q.filter(Asset.room_id == room_id)
    return q.limit(limit).all()

@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Get Asset Details",
    description="Retrieves a single campus asset by its unique UUID.",
    responses={
        404: {"description": "Asset not found"}
    }
)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    """
    Retrieve single asset record.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise EntityNotFoundError("Asset", asset_id)
    return asset

@router.get(
    "/{asset_id}/predictive-health",
    response_model=AssetPredictiveHealthResponse,
    summary="Get Asset Predictive Health Score",
    description="Detailed statistical health evaluation and 30-day failure risk for a specific asset based on age, failure history, and preventive maintenance records.",
    responses={
        404: {"description": "Asset not found"}
    }
)
def get_asset_predictive_health(asset_id: str, db: Session = Depends(get_db)):
    """
    Evaluate transparent multi-factor predictive health score for an asset.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise EntityNotFoundError("Asset", asset_id)
    return predictive_maintenance_service.evaluate_asset_health(db=db, asset=asset)
