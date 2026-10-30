import os
import sys

# Ensure backend root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.database.connection import engine, SessionLocal
from app.database.base import Base
# Import all models so Base has them registered
import app.database.models  # noqa
from app.database.seed.campus import seed_campus
from app.database.seed.rooms import seed_rooms
from app.database.seed.assets import seed_assets
from app.database.seed.users import seed_users
from app.database.seed.staff import seed_staff
from app.database.seed.inventory import seed_inventory
from app.database.seed.bookings import seed_bookings
from app.database.seed.incidents import seed_incidents
from app.database.seed.intelligence import seed_intelligence
from app.database.seed.enrich_faculty import seed_faculty_data

def reset_and_seed(verbose: bool = True):
    if verbose:
        print("[CampusOps Seed] Dropping existing database tables...")
    Base.metadata.drop_all(bind=engine)
    
    if verbose:
        print("[CampusOps Seed] Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if verbose:
            print("[CampusOps Seed] Seeding Buildings & Floors...")
        buildings, floors = seed_campus(db)

        if verbose:
            print("[CampusOps Seed] Seeding Rooms...")
        rooms = seed_rooms(db, buildings, floors)

        if verbose:
            print("[CampusOps Seed] Seeding Assets...")
        assets = seed_assets(db, rooms)

        if verbose:
            print("[CampusOps Seed] Seeding Users (Admins, Technicians, Faculty, Students)...")
        users_dict = seed_users(db, buildings, floors)

        if verbose:
            print("[CampusOps Seed] Seeding Staff Profiles & Skills...")
        seed_staff(db, users_dict["technicians"], buildings, floors)

        if verbose:
            print("[CampusOps Seed] Seeding Inventory Items...")
        inventory = seed_inventory(db)

        if verbose:
            print("[CampusOps Seed] Seeding Room Bookings...")
        seed_bookings(db, rooms, users_dict["faculty"])

        if verbose:
            print("[CampusOps Seed] Seeding Incidents, Reports, Work Orders & Approvals...")
        seed_incidents(db, rooms, assets, users_dict, inventory)

        if verbose:
            print("[CampusOps Seed] Seeding Faculty Academic Timetables, Reports & Notices...")
        seed_faculty_data(db, users_dict["faculty"], rooms)

        if verbose:
            print("[CampusOps Seed] Seeding Historical Intelligence Records...")
        seed_intelligence(db)

        db.commit()
        if verbose:
            print("==================================================")
            print("CampusOps Fictional University Dataset Seeded:")
            print(f" - Buildings: {len(buildings)}")
            print(f" - Floors: {len(floors)}")
            print(f" - Rooms: {len(rooms)}")
            print(f" - Users: {len(users_dict['all'])} (Students: {len(users_dict['students'])}, Faculty: {len(users_dict['faculty'])}, Staff/Tech: {len(users_dict['technicians'])}, Admins: {len(users_dict['admins'])})")
            print(f" - Assets: {len(assets)}")
            print(f" - Inventory Items: {len(inventory)}")
            print("==================================================")
    except Exception as e:
        db.rollback()
        print(f"[CampusOps Seed ERROR] {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    reset_and_seed()

