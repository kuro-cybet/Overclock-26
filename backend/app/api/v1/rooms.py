from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.room import Room
from app.database.models.campus import Building, Floor
from app.database.models.user import User
from app.schemas.room import RoomResponse, RoomReadinessUpdate
from app.core.exceptions import EntityNotFoundError
from app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.get("", response_model=List[RoomResponse])
def list_rooms(
    building_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    readiness: Optional[str] = Query(None),
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(Room)
    if building_id:
        q = q.filter(Room.building_id == building_id)
    if status:
        q = q.filter(Room.status == status)
    if readiness:
        q = q.filter(Room.daily_readiness_status == readiness)
    return q.limit(limit).all()

@router.get("/buildings")
def list_buildings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    buildings = db.query(Building).all()
    floors = db.query(Floor).all()
    res = []
    for b in buildings:
        b_floors = [f for f in floors if f.building_id == b.id]
        res.append({
            "id": b.id,
            "name": b.name,
            "code": b.code,
            "total_floors": b.total_floors,
            "description": b.description,
            "floors": [{"id": f.id, "floor_number": f.floor_number, "name": f.name} for f in b_floors]
        })
    return res

@router.get("/{room_id}", response_model=RoomResponse)
def get_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise EntityNotFoundError("Room", room_id)
    return room

@router.patch("/{room_id}/readiness", response_model=RoomResponse)
def update_room_readiness(
    room_id: str,
    payload: RoomReadinessUpdate,
    current_user: User = Depends(require_role(["admin", "technician"])),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise EntityNotFoundError("Room", room_id)

    room.daily_readiness_status = payload.daily_readiness_status
    room.readiness_checked_at = datetime.utcnow()
    room.readiness_checked_by = current_user.name
    db.commit()
    db.refresh(room)
    return room

