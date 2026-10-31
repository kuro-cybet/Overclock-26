import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.models.transport import (
    TransportRoute,
    TransportStop,
    TransportAllocation,
    TransportAnnouncement,
)
from app.core.exceptions import CampusOpsException

CHENNAI_ROUTES_SEED = [
    {
        "route_number": "RT-01",
        "route_name": "Tambaram - Campus Express",
        "origin": "Tambaram West",
        "destination": "Main Academic Campus Gate",
        "vehicle_number": "TN-01-CP-4521",
        "driver_name": "R. Murugan",
        "driver_phone": "+91 98401 22341",
        "capacity": 52,
        "operating_days": "Mon - Sat",
        "status": "active",
        "announcement": "Morning pickup punctuality strictly maintained. Please board 5 minutes before scheduled departure.",
        "stops": [
            {"stop_name": "Tambaram Sanatorium", "order": 1, "pickup": "07:15 AM", "drop": "05:45 PM", "landmark": "Opposite Railway Station"},
            {"stop_name": "Chromepet MIT Bridge", "order": 2, "pickup": "07:25 AM", "drop": "05:35 PM", "landmark": "Under MIT Flyover"},
            {"stop_name": "Pallavaram Signal", "order": 3, "pickup": "07:35 AM", "drop": "05:25 PM", "landmark": "GST Road Junction"},
            {"stop_name": "Guindy Kathipara", "order": 4, "pickup": "07:50 AM", "drop": "05:10 PM", "landmark": "Metro Station Gate 2"},
            {"stop_name": "Campus Main Gate", "order": 5, "pickup": "08:20 AM", "drop": "04:40 PM", "landmark": "Central Operations Porch"},
        ]
    },
    {
        "route_number": "RT-02",
        "route_name": "Velachery - OMR Tech Corridor",
        "origin": "Velachery Vijaya Nagar",
        "destination": "Main Academic Campus Gate",
        "vehicle_number": "TN-02-CP-8832",
        "driver_name": "K. Senthil",
        "driver_phone": "+91 98402 33452",
        "capacity": 55,
        "operating_days": "Mon - Sat",
        "status": "active",
        "announcement": "Operating via Rajiv Gandhi IT Expressway with reserved bus bay boarding.",
        "stops": [
            {"stop_name": "Velachery Vijaya Nagar", "order": 1, "pickup": "07:10 AM", "drop": "05:50 PM", "landmark": "Near MRTS Foot overbridge"},
            {"stop_name": "Thoraipakkam Toll Plaza", "order": 2, "pickup": "07:25 AM", "drop": "05:35 PM", "landmark": "200ft Radial Road Intersection"},
            {"stop_name": "Sholinganallur Junction", "order": 3, "pickup": "07:40 AM", "drop": "05:20 PM", "landmark": "TCS Gateway Side"},
            {"stop_name": "Siruseri IT Park Gate", "order": 4, "pickup": "07:55 AM", "drop": "05:05 PM", "landmark": "SIPCOT Main Arch"},
            {"stop_name": "Kelambakkam Junction", "order": 5, "pickup": "08:05 AM", "drop": "04:55 PM", "landmark": "Hospital Bus Stop"},
            {"stop_name": "Campus Main Gate", "order": 6, "pickup": "08:25 AM", "drop": "04:40 PM", "landmark": "Central Operations Porch"},
        ]
    },
    {
        "route_number": "RT-03",
        "route_name": "Adyar - ECR Coastal Route",
        "origin": "Adyar Depot",
        "destination": "Main Academic Campus Gate",
        "vehicle_number": "TN-06-CP-1904",
        "driver_name": "S. Prakash",
        "driver_phone": "+91 98403 44563",
        "capacity": 50,
        "operating_days": "Mon - Sat",
        "status": "active",
        "announcement": "Direct coastal arterial link servicing South Chennai faculty and scholars.",
        "stops": [
            {"stop_name": "Adyar Depot", "order": 1, "pickup": "07:15 AM", "drop": "05:45 PM", "landmark": "Near Lattice Bridge Road"},
            {"stop_name": "Thiruvanmiyur Bus Stand", "order": 2, "pickup": "07:25 AM", "drop": "05:35 PM", "landmark": "Opposite Marundeeswarar Temple"},
            {"stop_name": "Palavakkam", "order": 3, "pickup": "07:35 AM", "drop": "05:25 PM", "landmark": "ECR Main Road"},
            {"stop_name": "Neelankarai Signal", "order": 4, "pickup": "07:45 AM", "drop": "05:15 PM", "landmark": "Near Police Station"},
            {"stop_name": "Akkarai", "order": 5, "pickup": "07:55 AM", "drop": "05:05 PM", "landmark": "ECR-OMR Link Junction"},
            {"stop_name": "Campus Main Gate", "order": 6, "pickup": "08:20 AM", "drop": "04:40 PM", "landmark": "Central Operations Porch"},
        ]
    },
    {
        "route_number": "RT-04",
        "route_name": "Anna Nagar - Western Hub",
        "origin": "Anna Nagar Roundtana",
        "destination": "Main Academic Campus Gate",
        "vehicle_number": "TN-09-CP-6729",
        "driver_name": "M. Jayakumar",
        "driver_phone": "+91 98404 55674",
        "capacity": 55,
        "operating_days": "Mon - Sat",
        "status": "active",
        "announcement": "High-capacity transit vehicle equipped with emergency first aid and speed governor.",
        "stops": [
            {"stop_name": "Anna Nagar Roundtana", "order": 1, "pickup": "07:05 AM", "drop": "05:55 PM", "landmark": "Near Metro Entrance"},
            {"stop_name": "Koyambedu CMBT", "order": 2, "pickup": "07:20 AM", "drop": "05:40 PM", "landmark": "Rohini Theatre Flyover"},
            {"stop_name": "Porur Roundabout", "order": 3, "pickup": "07:40 AM", "drop": "05:20 PM", "landmark": "Mount-Poonamallee Road"},
            {"stop_name": "Poonamallee Bypass", "order": 4, "pickup": "07:55 AM", "drop": "05:05 PM", "landmark": "Kumananchavadi Junction"},
            {"stop_name": "Campus Main Gate", "order": 5, "pickup": "08:25 AM", "drop": "04:40 PM", "landmark": "Central Operations Porch"},
        ]
    },
    {
        "route_number": "RT-05",
        "route_name": "Chengalpattu - GST South Line",
        "origin": "Chengalpattu New Bus Stand",
        "destination": "Main Academic Campus Gate",
        "vehicle_number": "TN-11-CP-3108",
        "driver_name": "V. Annamalai",
        "driver_phone": "+91 98405 66785",
        "capacity": 50,
        "operating_days": "Mon - Sat",
        "status": "active",
        "announcement": "Covering southern residential suburban hubs along NH-45.",
        "stops": [
            {"stop_name": "Chengalpattu New Bus Stand", "order": 1, "pickup": "07:00 AM", "drop": "06:00 PM", "landmark": "Main Entrance"},
            {"stop_name": "Maraimalai Nagar", "order": 2, "pickup": "07:20 AM", "drop": "05:40 PM", "landmark": "Industrial Estate Flyover"},
            {"stop_name": "Guduvanchery", "order": 3, "pickup": "07:35 AM", "drop": "05:25 PM", "landmark": "Bus Terminus Footpath"},
            {"stop_name": "Vandalur Zoo", "order": 4, "pickup": "07:50 AM", "drop": "05:10 PM", "landmark": "Crescent University Gate"},
            {"stop_name": "Campus Main Gate", "order": 5, "pickup": "08:15 AM", "drop": "04:45 PM", "landmark": "Central Operations Porch"},
        ]
    }
]

class TransportService:
    @staticmethod
    def seed_default_routes(db: Session):
        """Seed authentic Chennai routes and sequence-ordered stops if table is empty."""
        if db.query(TransportRoute).first():
            return

        for r_data in CHENNAI_ROUTES_SEED:
            route = TransportRoute(
                id=str(uuid.uuid4()),
                route_number=r_data["route_number"],
                route_name=r_data["route_name"],
                origin=r_data["origin"],
                destination=r_data["destination"],
                vehicle_number=r_data["vehicle_number"],
                driver_name=r_data["driver_name"],
                driver_phone=r_data["driver_phone"],
                capacity=r_data["capacity"],
                operating_days=r_data["operating_days"],
                status=r_data["status"],
                announcement=r_data.get("announcement"),
                is_published=True
            )
            db.add(route)
            db.flush()

            for s_data in r_data["stops"]:
                stop = TransportStop(
                    id=str(uuid.uuid4()),
                    route_id=route.id,
                    stop_name=s_data["stop_name"],
                    sequence_order=s_data["order"],
                    pickup_time=s_data["pickup"],
                    drop_time=s_data["drop"],
                    landmark=s_data.get("landmark")
                )
                db.add(stop)

        # Seed global announcement
        ann = TransportAnnouncement(
            id=str(uuid.uuid4()),
            route_id=None,
            title="Monsoon Preparedness & Timetable Advisory",
            message="All University shuttles operate with geo-monitored routes and speed regulation. Please be at your scheduled stop 5 minutes before departure.",
            priority="normal"
        )
        db.add(ann)
        db.commit()

    @staticmethod
    def get_all_routes(db: Session, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve all published campus bus routes with sequence-ordered stops."""
        TransportService.seed_default_routes(db)

        query = db.query(TransportRoute).filter(TransportRoute.is_published == True)
        if search:
            s = f"%{search}%"
            query = query.filter(
                or_(
                    TransportRoute.route_number.like(s),
                    TransportRoute.route_name.like(s),
                    TransportRoute.origin.like(s),
                    TransportRoute.destination.like(s)
                )
            )

        routes = query.all()
        result = []

        for r in routes:
            stops = db.query(TransportStop).filter(
                TransportStop.route_id == r.id
            ).order_by(TransportStop.sequence_order.asc()).all()

            result.append({
                "id": r.id,
                "route_number": r.route_number,
                "route_name": r.route_name,
                "origin": r.origin,
                "destination": r.destination,
                "vehicle_number": r.vehicle_number,
                "driver_name": r.driver_name,
                "driver_phone": r.driver_phone,
                "capacity": r.capacity,
                "operating_days": r.operating_days,
                "status": r.status,
                "announcement": r.announcement,
                "stops": [
                    {
                        "id": s.id,
                        "stop_name": s.stop_name,
                        "sequence_order": s.sequence_order,
                        "pickup_time": s.pickup_time,
                        "drop_time": s.drop_time,
                        "landmark": s.landmark
                    }
                    for s in stops
                ]
            })

        return result

    @staticmethod
    def get_user_assignment(db: Session, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve transport allocation for a specific student or faculty member."""
        TransportService.seed_default_routes(db)

        alloc = db.query(TransportAllocation).filter(
            TransportAllocation.user_id == user_id,
            TransportAllocation.status == "active"
        ).first()

        # If user has no allocation, assign Route 1, Stop 1 by default
        if not alloc:
            first_route = db.query(TransportRoute).first()
            if first_route:
                first_stop = db.query(TransportStop).filter(
                    TransportStop.route_id == first_route.id
                ).first()
                if first_stop:
                    alloc = TransportAllocation(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        route_id=first_route.id,
                        stop_id=first_stop.id,
                        academic_year="2026-2027",
                        status="active",
                        fee_status="paid"
                    )
                    db.add(alloc)
                    db.commit()
                    db.refresh(alloc)

        if not alloc:
            return None

        route = db.query(TransportRoute).filter(TransportRoute.id == alloc.route_id).first()
        stop = db.query(TransportStop).filter(TransportStop.id == alloc.stop_id).first()

        return {
            "allocation_id": alloc.id,
            "status": alloc.status,
            "fee_status": alloc.fee_status,
            "academic_year": alloc.academic_year,
            "route": {
                "id": route.id if route else None,
                "route_number": route.route_number if route else "TBD",
                "route_name": route.route_name if route else "Assigned Route",
                "vehicle_number": route.vehicle_number if route else "TBD",
                "driver_name": route.driver_name if route else "Staff Driver",
                "driver_phone": route.driver_phone if route else "University Helpdesk",
                "status": route.status if route else "active",
            },
            "stop": {
                "id": stop.id if stop else None,
                "stop_name": stop.stop_name if stop else "Designated Campus Stop",
                "pickup_time": stop.pickup_time if stop else "07:30 AM",
                "drop_time": stop.drop_time if stop else "05:30 PM",
                "landmark": stop.landmark if stop else None
            }
        }

    @staticmethod
    def get_announcements(db: Session, route_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve transport service announcements."""
        TransportService.seed_default_routes(db)

        query = db.query(TransportAnnouncement)
        if route_id:
            query = query.filter(or_(TransportAnnouncement.route_id == route_id, TransportAnnouncement.route_id.is_(None)))

        announcements = query.order_by(TransportAnnouncement.created_at.desc()).all()
        return [
            {
                "id": a.id,
                "title": a.title,
                "message": a.message,
                "priority": a.priority,
                "route_id": a.route_id,
                "created_at": a.created_at.isoformat()
            }
            for a in announcements
        ]

