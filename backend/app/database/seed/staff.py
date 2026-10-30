import json
from sqlalchemy.orm import Session
from app.database.models.staff import StaffProfile

def seed_staff(db: Session, technicians, buildings, floors):
    profiles = []
    shifts = ["morning", "evening", "night"]
    skill_sets = [
        ["network", "wifi", "hardware", "electrical"],
        ["electrical", "hvac", "power_distribution"],
        ["general_cleaning", "sanitation", "waste_management"],
        ["exam_setup", "av_equipment", "classroom_readiness"],
        ["plumbing", "water_systems", "sanitary_maintenance"],
        ["network", "cabling", "router_config", "hardware"]
    ]

    for idx, tech in enumerate(technicians):
        building = buildings[idx % len(buildings)]
        floor = next((f for f in floors if f.building_id == building.id), floors[0])
        skills = skill_sets[idx % len(skill_sets)]
        
        # David Miller specific setup
        if tech.email == "tech@campusops.edu":
            skills = ["network", "wifi", "hardware", "electrical", "exam_setup"]

        profile = StaffProfile(
            user_id=tech.id,
            skills=json.dumps(skills),
            shift=shifts[idx % len(shifts)],
            assigned_building_id=building.id,
            assigned_floor_id=floor.id,
            availability_status="available" if idx % 6 != 0 else "on_task",
            current_workload=0
        )
        db.add(profile)
        profiles.append(profile)

    db.flush()
    return profiles

