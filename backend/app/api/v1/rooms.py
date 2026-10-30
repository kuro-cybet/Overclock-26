from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.room import Room
from app.database.models.campus import Building, Floor
from app.database.models.user import User
from app.schemas.room import RoomResponse, RoomReadinessUpdate, BuildingSummaryResponse
from app.core.exceptions import EntityNotFoundError
from app.api.deps import get_current_user

router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.get(
    "",
    response_model=List[RoomResponse],
    summary="List Campus Rooms",
    description="Retrieves classrooms, lecture halls, laboratories, and offices across campus buildings."
)
def list_rooms(
    building_id: Optional[str] = Query(None, description="Filter by campus building UUID"),
    status: Optional[str] = Query(None, description="Filter by operational status: `available`, `occupied`, `under_maintenance`, `out_of_order`"),
    readiness: Optional[str] = Query(None, description="Filter by readiness: `confirmed_today`, `unconfirmed`, `stale`, `unavailable`"),
    limit: int = Query(100, ge=1, le=500, description="Maximum rooms to return"),
    db: Session = Depends(get_db)
):
    """
    List rooms with operational readiness and seating capacity.
    """
    q = db.query(Room)
    if building_id:
        q = q.filter(Room.building_id == building_id)
    if status:
        q = q.filter(Room.status == status)
    if readiness:
        q = q.filter(Room.daily_readiness_status == readiness)
    return q.limit(limit).all()

@router.get(
    "/buildings",
    response_model=List[BuildingSummaryResponse],
    summary="List Campus Buildings and Floors",
    description="Retrieves the physical hierarchy of campus buildings with nested floor lists."
)
def list_buildings(db: Session = Depends(get_db)):
    """
    List campus buildings with their associated floor structures.
    """
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

@router.get(
    "/{room_id}",
    response_model=RoomResponse,
    summary="Get Room Details by ID",
    description="Retrieves room profile, capacity, and current daily readiness status.",
    responses={
        404: {"description": "Room not found"}
    }
)
def get_room(room_id: str, db: Session = Depends(get_db)):
    """
    Retrieve single room entity by UUID.
    """
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise EntityNotFoundError("Room", room_id)
    return room

@router.patch(
    "/{room_id}/readiness",
    response_model=RoomResponse,
    summary="Update Room Daily Readiness Status",
    description="Updates the physical daily readiness check status of a room (e.g. `confirmed_today`, `stale`, `unconfirmed`).",
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Room not found"}
    }
)
def update_room_readiness(
    room_id: str,
    payload: RoomReadinessUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update daily physical verification status of a room.
    """
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise EntityNotFoundError("Room", room_id)

    room.daily_readiness_status = payload.daily_readiness_status
    room.readiness_checked_at = datetime.utcnow()
    room.readiness_checked_by = current_user.name
    db.commit()
    db.refresh(room)
    return room
