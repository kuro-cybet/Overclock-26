from sqlalchemy.orm import Session
from app.database.models.campus import Building, Floor

BUILDING_DEFINITIONS = [
    {"name": "Engineering Block", "code": "ENG", "total_floors": 3, "description": "Faculty of Engineering, Computer Science labs & Robotics"},
    {"name": "Science Block", "code": "SCI", "total_floors": 3, "description": "Physics, Chemistry and Biological Science Laboratories"},
    {"name": "Library Block", "code": "LIB", "total_floors": 3, "description": "Central Campus Library, Archives, Media Rooms & Study Desks"},
    {"name": "Humanities Block", "code": "HUM", "total_floors": 3, "description": "Social Sciences, Arts, Language Labs & Lecture Theatres"},
    {"name": "Administration Block", "code": "ADM", "total_floors": 3, "description": "Chancellor Office, Registrar, Admissions, IT Operations"},
    {"name": "Innovation Block", "code": "INN", "total_floors": 3, "description": "Startup Incubator, Maker Space, High-Performance Computing"}
]

def seed_campus(db: Session):
    buildings = []
    floors = []
    for b_data in BUILDING_DEFINITIONS:
        b = Building(
            name=b_data["name"],
            code=b_data["code"],
            total_floors=b_data["total_floors"],
            description=b_data["description"]
        )
        db.add(b)
        db.flush()
        buildings.append(b)

        for f_num in range(1, b_data["total_floors"] + 1):
            floor = Floor(
                building_id=b.id,
                floor_number=f_num,
                name=f"Level {f_num} - {b.code}"
            )
            db.add(floor)
            db.flush()
            floors.append(floor)

    return buildings, floors

