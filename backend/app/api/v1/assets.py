from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.asset import Asset
from app.core.exceptions import EntityNotFoundError
from app.services.predictive_maintenance_service import predictive_maintenance_service
from app.database.models.user import User
from app.api.deps import require_role

router = APIRouter(prefix="/assets", tags=["assets"])

@router.get("/predictive-overview")
def get_predictive_fleet_overview(
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    Fleet-wide predictive maintenance status: healthy, attention required,
    high risk assets, 30-day failure probabilities, and upcoming PM schedules.
    """
    return predictive_maintenance_service.get_fleet_predictive_overview(db=db)

@router.get("")
def list_assets(
    category: Optional[str] = Query(None),
    building_id: Optional[str] = Query(None),
    room_id: Optional[str] = Query(None),
    limit: int = 150,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    q = db.query(Asset)
    if category:
        q = q.filter(Asset.category == category)
    if building_id:
        q = q.filter(Asset.building_id == building_id)
    if room_id:
        q = q.filter(Asset.room_id == room_id)
    return q.limit(limit).all()

@router.get("/{asset_id}")
def get_asset(
    asset_id: str,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise EntityNotFoundError("Asset", asset_id)
    return asset

@router.get("/{asset_id}/predictive-health")
def get_asset_predictive_health(
    asset_id: str,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Detailed statistical health evaluation and 30-day failure risk for a specific asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise EntityNotFoundError("Asset", asset_id)
    return predictive_maintenance_service.evaluate_asset_health(db=db, asset=asset)
