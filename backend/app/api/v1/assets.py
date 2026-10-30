from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.asset import Asset
from app.core.exceptions import EntityNotFoundError

router = APIRouter(prefix="/assets", tags=["assets"])

@router.get("")
def list_assets(
    category: Optional[str] = Query(None),
    building_id: Optional[str] = Query(None),
    room_id: Optional[str] = Query(None),
    limit: int = 150,
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
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise EntityNotFoundError("Asset", asset_id)
    return asset

