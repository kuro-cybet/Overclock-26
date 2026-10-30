import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.models.room import Room

def seed_rooms(db: Session, buildings, floors):
    rooms = []
    building_map = {b.code: [f for f in floors if f.building_id == b.id] for b in buildings}

    room_templates = [
        # ENG (10 rooms)
        {"b": "ENG", "floor_idx": 0, "num": "101", "name": "Computer Lab A", "type": "lab", "cap": 60, "features": ["wifi", "lab_pcs", "ac", "projector"]},
        {"b": "ENG", "floor_idx": 0, "num": "102", "name": "Computer Lab B", "type": "lab", "cap": 60, "features": ["wifi", "lab_pcs", "ac", "projector"]},
        {"b": "ENG", "floor_idx": 0, "num": "103", "name": "Robotics Workshop", "type": "lab", "cap": 30, "features": ["wifi", "3d_printers", "power_bench"]},
        {"b": "ENG", "floor_idx": 0, "num": "104", "name": "Engineering Lecture Hall 1", "type": "exam_hall", "cap": 120, "features": ["wifi", "projector", "sound_system", "ac"]},
        {"b": "ENG", "floor_idx": 1, "num": "201", "name": "Software Engineering Studio", "type": "classroom", "cap": 45, "features": ["wifi", "smartboard", "ac"]},
        {"b": "ENG", "floor_idx": 1, "num": "202", "name": "Embedded Systems Lab", "type": "lab", "cap": 35, "features": ["wifi", "oscilloscopes", "ac"]},
        {"b": "ENG", "floor_idx": 1, "num": "203", "name": "Seminar Room E-203", "type": "seminar_hall", "cap": 50, "features": ["wifi", "projector", "ac"]},
        {"b": "ENG", "floor_idx": 2, "num": "301", "name": "Engineering Examination Hall", "type": "exam_hall", "cap": 150, "features": ["wifi", "sound_system", "ac", "cctv"]},
        {"b": "ENG", "floor_idx": 2, "num": "302", "name": "Postgrad Research Hub", "type": "lab", "cap": 25, "features": ["wifi", "ac", "workstations"]},
        {"b": "ENG", "floor_idx": 2, "num": "303", "name": "Faculty Boardroom E", "type": "faculty_room", "cap": 20, "features": ["wifi", "teleconference", "ac"]},

        # SCI (10 rooms)
        {"b": "SCI", "floor_idx": 0, "num": "101", "name": "General Chemistry Lab", "type": "lab", "cap": 40, "features": ["fume_hoods", "gas_line", "eyewash", "ac"]},
        {"b": "SCI", "floor_idx": 0, "num": "102", "name": "Organic Synthesis Lab", "type": "lab", "cap": 35, "features": ["fume_hoods", "spectrometer", "ac"]},
        {"b": "SCI", "floor_idx": 0, "num": "103", "name": "Science Lecture Theatre 1", "type": "classroom", "cap": 100, "features": ["wifi", "projector", "ac"]},
        {"b": "SCI", "floor_idx": 1, "num": "201", "name": "Physics Optics Lab", "type": "lab", "cap": 30, "features": ["darkroom", "lasers", "ac"]},
        {"b": "SCI", "floor_idx": 1, "num": "202", "name": "Modern Physics Lab", "type": "lab", "cap": 30, "features": ["wifi", "sensors", "ac"]},
        {"b": "SCI", "floor_idx": 1, "num": "203", "name": "Science Seminar Room 203", "type": "seminar_hall", "cap": 60, "features": ["wifi", "projector", "ac"]},
        {"b": "SCI", "floor_idx": 1, "num": "204", "name": "Science Classroom 204", "type": "classroom", "cap": 45, "features": ["wifi", "smartboard", "ac"]},
        {"b": "SCI", "floor_idx": 2, "num": "301", "name": "Biochemistry Lab", "type": "lab", "cap": 35, "features": ["centrifuges", "refrigeration", "ac"]},
        {"b": "SCI", "floor_idx": 2, "num": "302", "name": "Molecular Biology Suite", "type": "lab", "cap": 25, "features": ["pcr_machines", "biosafety_cabinet"]},
        {"b": "SCI", "floor_idx": 2, "num": "303", "name": "Science Exam Hall 303", "type": "exam_hall", "cap": 120, "features": ["wifi", "ac", "cctv"]},

        # LIB (10 rooms)
        {"b": "LIB", "floor_idx": 0, "num": "101", "name": "Central Reading Room", "type": "classroom", "cap": 120, "features": ["wifi", "quiet_zone", "ac"]},
        {"b": "LIB", "floor_idx": 0, "num": "102", "name": "Digital Archives Lab", "type": "lab", "cap": 30, "features": ["wifi", "scanners", "workstations"]},
        {"b": "LIB", "floor_idx": 0, "num": "103", "name": "Library Audio-Visual Suite", "type": "seminar_hall", "cap": 40, "features": ["wifi", "av_system", "ac"]},
        {"b": "LIB", "floor_idx": 1, "num": "201", "name": "Collaborative Study Hall A", "type": "classroom", "cap": 50, "features": ["wifi", "whiteboards", "ac"]},
        {"b": "LIB", "floor_idx": 1, "num": "202", "name": "Collaborative Study Hall B", "type": "classroom", "cap": 50, "features": ["wifi", "whiteboards", "ac"]},
        {"b": "LIB", "floor_idx": 1, "num": "203", "name": "Research Commons 203", "type": "classroom", "cap": 40, "features": ["wifi", "charging_ports", "ac"]},
        {"b": "LIB", "floor_idx": 1, "num": "204", "name": "Multimedia Production Studio", "type": "lab", "cap": 20, "features": ["soundproofing", "video_rigs", "ac"]},
        {"b": "LIB", "floor_idx": 2, "num": "301", "name": "Quiet Graduate Reading Room", "type": "classroom", "cap": 60, "features": ["wifi", "carrels", "ac"]},
        {"b": "LIB", "floor_idx": 2, "num": "302", "name": "Special Collections Archive", "type": "utility", "cap": 15, "features": ["climate_controlled", "rfid"]},
        {"b": "LIB", "floor_idx": 2, "num": "303", "name": "Library Seminar Gallery", "type": "seminar_hall", "cap": 80, "features": ["wifi", "projector", "ac"]},

        # HUM (10 rooms)
        {"b": "HUM", "floor_idx": 0, "num": "101", "name": "Humanities Auditorium", "type": "exam_hall", "cap": 180, "features": ["wifi", "sound_system", "dual_projectors", "ac"]},
        {"b": "HUM", "floor_idx": 0, "num": "102", "name": "Language Lab 102", "type": "lab", "cap": 40, "features": ["wifi", "audio_stations", "ac"]},
        {"b": "HUM", "floor_idx": 0, "num": "103", "name": "History Discussion Hall", "type": "classroom", "cap": 50, "features": ["wifi", "smartboard", "ac"]},
        {"b": "HUM", "floor_idx": 1, "num": "201", "name": "Philosophy Seminar Room", "type": "seminar_hall", "cap": 35, "features": ["wifi", "ac"]},
        {"b": "HUM", "floor_idx": 1, "num": "202", "name": "Literature Lecture Room 202", "type": "classroom", "cap": 55, "features": ["wifi", "projector", "ac"]},
        {"b": "HUM", "floor_idx": 1, "num": "203", "name": "Sociology Workshop Space", "type": "classroom", "cap": 40, "features": ["wifi", "movable_desks", "ac"]},
        {"b": "HUM", "floor_idx": 1, "num": "204", "name": "Cultural Studies Lab", "type": "lab", "cap": 30, "features": ["wifi", "av_monitors", "ac"]},
        {"b": "HUM", "floor_idx": 2, "num": "301", "name": "Fine Arts Studio", "type": "classroom", "cap": 30, "features": ["natural_lighting", "easels", "washbasin"]},
        {"b": "HUM", "floor_idx": 2, "num": "302", "name": "Performing Arts Rehearsal Hall", "type": "seminar_hall", "cap": 60, "features": ["mirrors", "sound_system", "ac"]},
        {"b": "HUM", "floor_idx": 2, "num": "303", "name": "Humanities Exam Hall 303", "type": "exam_hall", "cap": 100, "features": ["wifi", "cctv", "ac"]},

        # ADM (10 rooms)
        {"b": "ADM", "floor_idx": 0, "num": "101", "name": "Visitor Briefing Centre", "type": "seminar_hall", "cap": 50, "features": ["wifi", "display_panels", "ac"]},
        {"b": "ADM", "floor_idx": 0, "num": "102", "name": "Admissions Service Hall", "type": "classroom", "cap": 70, "features": ["wifi", "ticket_kiosk", "ac"]},
        {"b": "ADM", "floor_idx": 0, "num": "103", "name": "Campus Security & Dispatch", "type": "utility", "cap": 20, "features": ["cctv_monitors", "backup_power", "ac"]},
        {"b": "ADM", "floor_idx": 1, "num": "201", "name": "Registrar Records Room", "type": "utility", "cap": 25, "features": ["fireproof_storage", "rfid"]},
        {"b": "ADM", "floor_idx": 1, "num": "202", "name": "Operations Command Room", "type": "seminar_hall", "cap": 30, "features": ["wifi", "dashboard_video_wall", "ac"]},
        {"b": "ADM", "floor_idx": 1, "num": "203", "name": "Finance & Bursar Office", "type": "faculty_room", "cap": 30, "features": ["wifi", "secure_terminals", "ac"]},
        {"b": "ADM", "floor_idx": 1, "num": "204", "name": "HR & Staff Services", "type": "faculty_room", "cap": 25, "features": ["wifi", "ac"]},
        {"b": "ADM", "floor_idx": 2, "num": "301", "name": "Executive Council Chamber", "type": "seminar_hall", "cap": 40, "features": ["wifi", "conferencing", "ac"]},
        {"b": "ADM", "floor_idx": 2, "num": "302", "name": "Campus IT Data Operations", "type": "lab", "cap": 20, "features": ["server_racks", "ups", "biometrics"]},
        {"b": "ADM", "floor_idx": 2, "num": "303", "name": "Administrative Training Suite", "type": "classroom", "cap": 40, "features": ["wifi", "projector", "ac"]},

        # INN (10 rooms)
        {"b": "INN", "floor_idx": 0, "num": "101", "name": "Maker Space Fabrication Lab", "type": "lab", "cap": 40, "features": ["cnc_machine", "laser_cutter", "soldering"]},
        {"b": "INN", "floor_idx": 0, "num": "102", "name": "Startup Incubation Co-work 1", "type": "classroom", "cap": 60, "features": ["wifi", "whiteboards", "ac"]},
        {"b": "INN", "floor_idx": 0, "num": "103", "name": "Pitch Arena & Showcase", "type": "exam_hall", "cap": 100, "features": ["wifi", "stage_lighting", "audio_rig", "ac"]},
        {"b": "INN", "floor_idx": 1, "num": "201", "name": "HPC & AI Simulation Lab", "type": "lab", "cap": 40, "features": ["gpu_clusters", "cooling", "gigabit_lan"]},
        {"b": "INN", "floor_idx": 1, "num": "202", "name": "VR & Augmented Reality Lab", "type": "lab", "cap": 30, "features": ["motion_trackers", "headsets", "ac"]},
        {"b": "INN", "floor_idx": 1, "num": "203", "name": "Startup Incubation Co-work 2", "type": "classroom", "cap": 50, "features": ["wifi", "ac"]},
        {"b": "INN", "floor_idx": 1, "num": "204", "name": "Innovation Brainstorm Pod", "type": "seminar_hall", "cap": 25, "features": ["wifi", "interactive_wall", "ac"]},
        {"b": "INN", "floor_idx": 2, "num": "301", "name": "Cleanroom Prototyping", "type": "lab", "cap": 20, "features": ["hepa_filters", "airlock", "clean_benches"]},
        {"b": "INN", "floor_idx": 2, "num": "302", "name": "IoT Hardware Lab", "type": "lab", "cap": 35, "features": ["spectrum_analyzers", "soldering", "wifi"]},
        {"b": "INN", "floor_idx": 2, "num": "303", "name": "Venture Collaboration Suite", "type": "faculty_room", "cap": 30, "features": ["wifi", "teleconference", "ac"]},
    ]

    # Status distribution to showcase confirmed, stale, unconfirmed readiness
    readiness_states = ["confirmed", "stale", "unconfirmed"]
    now = datetime.utcnow()

    for idx, tmpl in enumerate(room_templates):
        b_code = tmpl["b"]
        floors_for_b = building_map[b_code]
        floor = floors_for_b[tmpl["floor_idx"]]

        readiness = readiness_states[idx % 3]
        if readiness == "confirmed":
            checked_at = now - timedelta(hours=2)
        elif readiness == "stale":
            checked_at = now - timedelta(hours=28)
        else:
            checked_at = None

        room = Room(
            building_id=floor.building_id,
            floor_id=floor.id,
            room_number=f"{b_code}-{tmpl['num']}",
            name=tmpl["name"],
            type=tmpl["type"],
            capacity=tmpl["cap"],
            features=json.dumps(tmpl["features"]),
            status="available" if idx % 7 != 0 else "under_maintenance",
            daily_readiness_status=readiness,
            freshness_state="confirmed_today" if readiness == "confirmed" else ("stale" if readiness == "stale" else "unconfirmed"),
            last_confirmed_at=checked_at,
            confirmed_by="Floor Incharge Santos" if checked_at else None,
            freshness_source="daily_inspection",
            readiness_checked_at=checked_at,
            readiness_checked_by="tech-floor-1" if checked_at else None
        )
        db.add(room)
        db.flush()
        rooms.append(room)

    return rooms

