from sqlalchemy.orm import Session
from app.database.models.user import User
from app.core.security import hash_password

def seed_users(db: Session, buildings, floors):
    users = []
    default_pw_hash = hash_password("password123")

    eng_b = buildings[0]
    eng_f1 = floors[0]

    # --- ADMINS (4 distinct sub-roles) ---
    admins_data = [
        {"email": "admin@campusops.edu", "name": "Dr. Sarah Mitchell", "role": "admin", "sub_role": "system_admin", "dept": "Central Operations"},
        {"email": "sysadmin@campusops.edu", "name": "Alex Vance", "role": "admin", "sub_role": "system_admin", "dept": "IT Systems"},
        {"email": "dept_mgr@campusops.edu", "name": "Prof. Arthur Pendelton", "role": "admin", "sub_role": "department_manager", "dept": "Engineering"},
        {"email": "facilities@campusops.edu", "name": "Elena Rostova", "role": "admin", "sub_role": "facilities_admin", "dept": "Facilities Management"},
        {"email": "procurement@campusops.edu", "name": "Marcus Sterling", "role": "admin", "sub_role": "procurement_approver", "dept": "Procurement & Finance"},
    ]

    for a in admins_data:
        u = User(
            email=a["email"],
            name=a["name"],
            hashed_password=default_pw_hash,
            role=a["role"],
            sub_role=a["sub_role"],
            department=a["dept"],
            building_id=eng_b.id,
            floor_id=eng_f1.id
        )
        db.add(u)
        users.append(u)

    # --- TECHNICIANS & SUPPORT STAFF (24 users) ---
    tech_sub_roles = ["floor_incharge", "maintenance_technician", "janitor", "room_incharge"]
    
    # Key demo technicians:
    named_techs = [
        {"email": "tech@campusops.edu", "name": "David Miller", "sub_role": "maintenance_technician"},
        {"email": "maintenance@campusops.edu", "name": "John Kowalski", "sub_role": "maintenance_technician"},
        {"email": "floor_incharge@campusops.edu", "name": "Maria Santos", "sub_role": "floor_incharge"},
        {"email": "janitor@campusops.edu", "name": "Bob Jenkins", "sub_role": "janitor"},
        {"email": "room_incharge@campusops.edu", "name": "Chloe Bennett", "sub_role": "room_incharge"},
    ]

    technicians = []
    for t in named_techs:
        u = User(
            email=t["email"],
            name=t["name"],
            hashed_password=default_pw_hash,
            role="technician",
            sub_role=t["sub_role"],
            department="Campus Operations",
            building_id=eng_b.id,
            floor_id=eng_f1.id
        )
        db.add(u)
        users.append(u)
        technicians.append(u)

    for i in range(len(named_techs) + 1, 25):
        sub_r = tech_sub_roles[i % len(tech_sub_roles)]
        building = buildings[i % len(buildings)]
        floor = next((f for f in floors if f.building_id == building.id), eng_f1)
        u = User(
            email=f"tech{i}@campusops.edu",
            name=f"Technician {i}",
            hashed_password=default_pw_hash,
            role="technician",
            sub_role=sub_r,
            department="Campus Maintenance",
            building_id=building.id,
            floor_id=floor.id
        )
        db.add(u)
        users.append(u)
        technicians.append(u)

    # --- FACULTY (40 users) ---
    named_faculty = [
        {"email": "faculty@campusops.edu", "name": "Prof. Alistair Finch", "dept": "Computer Science"},
        {"email": "prof.smith@campusops.edu", "name": "Dr. Eleanor Smith", "dept": "Electrical Engineering"},
        {"email": "prof.chen@campusops.edu", "name": "Dr. Wei Chen", "dept": "Mechanical Engineering"},
        {"email": "prof.kumar@campusops.edu", "name": "Dr. Rajesh Kumar", "dept": "Physics"},
    ]
    faculty_list = []
    for f in named_faculty:
        u = User(
            email=f["email"],
            name=f["name"],
            hashed_password=default_pw_hash,
            role="faculty",
            sub_role=None,
            department=f["dept"],
            building_id=eng_b.id,
            floor_id=eng_f1.id
        )
        db.add(u)
        users.append(u)
        faculty_list.append(u)

    departments = ["Computer Science", "Electrical Eng", "Physics", "Chemistry", "Mathematics", "Humanities", "Business", "Bioengineering"]
    for i in range(len(named_faculty) + 1, 41):
        dept = departments[i % len(departments)]
        building = buildings[i % len(buildings)]
        u = User(
            email=f"faculty{i}@campusops.edu",
            name=f"Faculty Member {i}",
            hashed_password=default_pw_hash,
            role="faculty",
            sub_role=None,
            department=dept,
            building_id=building.id,
            floor_id=floors[0].id
        )
        db.add(u)
        users.append(u)
        faculty_list.append(u)

    # --- STUDENTS (500 users) ---
    key_students = [
        {"email": "student@campusops.edu", "name": "Jordan Lee", "dept": "Computer Science"},
        {"email": "student1@campusops.edu", "name": "Samantha Green", "dept": "Electrical Eng"},
        {"email": "student2@campusops.edu", "name": "Liam Patel", "dept": "Mechanical Eng"},
    ]
    student_list = []
    for s in key_students:
        u = User(
            email=s["email"],
            name=s["name"],
            hashed_password=default_pw_hash,
            role="student",
            sub_role=None,
            department=s["dept"],
            building_id=eng_b.id,
            floor_id=eng_f1.id
        )
        db.add(u)
        users.append(u)
        student_list.append(u)

    for i in range(len(key_students) + 1, 501):
        dept = departments[i % len(departments)]
        u = User(
            email=f"student{i}@campusops.edu",
            name=f"Student {i}",
            hashed_password=default_pw_hash,
            role="student",
            sub_role=None,
            department=dept,
            building_id=buildings[i % len(buildings)].id,
            floor_id=floors[0].id
        )
        db.add(u)
        users.append(u)
        student_list.append(u)

    db.flush()
    return {
        "all": users,
        "admins": [u for u in users if u.role == "admin"],
        "technicians": technicians,
        "faculty": faculty_list,
        "students": student_list
    }

