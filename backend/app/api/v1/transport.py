from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Body, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.api.deps import get_current_user
from app.database.models.user import User
from app.services.transport_service import TransportService
from app.core.exceptions import CampusOpsException

router = APIRouter(prefix="/transport", tags=["Chennai Campus Transportation"])

class TransportRouteCreate(BaseModel):
    id: Optional[str] = None
    route_number: str
    route_name: str
    origin: str
    destination: str = "Campus Main Gate"
    vehicle_number: str
    driver_name: str
    driver_phone: str
    capacity: int = 50
    operating_days: str = "Mon-Sat"
    status: str = "active"
    announcement: Optional[str] = None
    is_published: bool = True

@router.get("/routes", summary="List All Chennai Bus Routes & Stops")
def get_routes(
    search: Optional[str] = Query(None, description="Search route name, number, or stop area"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns sequence-ordered Chennai campus bus routes, pickup/drop times, and driver contacts."""
    return TransportService.get_all_routes(db, search=search)

@router.get("/my-assignment", summary="User Transport Allocation")
def get_my_assignment(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns assigned route, pickup stop, and pass status for student or faculty member."""
    res = TransportService.get_user_assignment(db, current_user.id)
    if not res:
        return {"assigned": False, "message": "No transport allocation recorded for current academic term."}
    return {"assigned": True, "allocation": res}

@router.get("/announcements", summary="Transport Alerts & Monsoon Advisories")
def get_announcements(
    route_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Active traffic advisories, route detours, or schedule changes."""
    return TransportService.get_announcements(db, route_id=route_id)

@router.post("/routes", summary="Admin Manage Transport Route")
def save_route(
    payload: TransportRouteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enforces admin privilege to add or modify campus transit routes."""
    if current_user.role != "admin":
        raise CampusOpsException(
            status_code=403,
            detail="Forbidden: Only administrators can configure campus bus routes."
        )

    # Simple admin create / update
    from app.database.models.transport import TransportRoute
    import uuid

    if payload.id:
        route = db.query(TransportRoute).filter(TransportRoute.id == payload.id).first()
        if not route:
            raise CampusOpsException(status_code=404, detail="Route not found")
        route.route_number = payload.route_number
        route.route_name = payload.route_name
        route.origin = payload.origin
        route.destination = payload.destination
        route.vehicle_number = payload.vehicle_number
        route.driver_name = payload.driver_name
        route.driver_phone = payload.driver_phone
        route.capacity = payload.capacity
        route.operating_days = payload.operating_days
        route.status = payload.status
        route.announcement = payload.announcement
        route.is_published = payload.is_published
    else:
        route = TransportRoute(
            id=str(uuid.uuid4()),
            route_number=payload.route_number,
            route_name=payload.route_name,
            origin=payload.origin,
            destination=payload.destination,
            vehicle_number=payload.vehicle_number,
            driver_name=payload.driver_name,
            driver_phone=payload.driver_phone,
            capacity=payload.capacity,
            operating_days=payload.operating_days,
            status=payload.status,
            announcement=payload.announcement,
            is_published=payload.is_published
        )
        db.add(route)

    db.commit()
    db.refresh(route)
    return {"status": "success", "route_id": route.id}
