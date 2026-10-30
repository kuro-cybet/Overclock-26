import json
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.models.user import User
from app.database.models.room import Room
from app.database.models.booking import RoomBooking
from app.database.models.report import Report
from app.database.models.notification import Notification

def seed_faculty_data(db: Session, faculty_users, rooms):
    if not faculty_users or not rooms:
        return

    faculty = faculty_users[0]  # Prof Finch
    now = datetime.utcnow()

    courses = [
        ("CS304: Distributed Systems Midterm Examination", "examination", ["wifi", "lab_pcs", "ac"]),
        ("CS101: Introduction to Computing Lecture", "lecture", ["projector", "wifi"]),
        ("CS201: Data Structures and Algorithms Lab", "lab_session", ["lab_pcs", "wifi"]),
        ("CS401: Advanced Artificial Intelligence Workshop", "seminar", ["projector", "smartboard"]),
        ("CS305: Database Management Systems Practical", "lab_session", ["lab_pcs", "projector"]),
        ("CS310: Computer Networks Protocol Testing", "lab_session", ["lab_pcs", "ethernet"]),
        ("CS450: Machine Learning Final Assessment", "examination", ["lab_pcs", "wifi", "ac"]),
        ("CS102: Object Oriented Programming Lab", "lab_session", ["lab_pcs", "wifi"]),
        ("CS320: Software Engineering Team Sprint Review", "meeting", ["projector", "smartboard"]),
        ("CS499: Senior Capstone Project Defense", "seminar", ["projector", "podium"]),
        ("CS205: Discrete Mathematics Tutorial", "lecture", ["whiteboard", "projector"]),
        ("CS430: Cloud Computing Infrastructure Lab", "lab_session", ["lab_pcs", "wifi"]),
        ("CS340: Cyber Security Penetration Lab", "lab_session", ["lab_pcs", "firewall"]),
        ("CS412: Natural Language Processing Seminar", "seminar", ["projector", "mic"]),
        ("CS380: Web Application Architecture", "lecture", ["projector", "wifi"]),
        ("CS250: Operating Systems Kernel Programming", "lab_session", ["lab_pcs", "wifi"]),
        ("CS490: Undergraduate Research Symposium", "seminar", ["projector", "mic", "podium"]),
        ("CS110: Computational Thinking & Python Lab", "lab_session", ["lab_pcs"]),
        ("CS360: Mobile Application Engineering", "lecture", ["projector", "wifi"]),
        ("CS498: Comprehensive Technical Viva Voce", "examination", ["projector", "ac"]),
    ]

    for i, (title, purpose, eq) in enumerate(courses):
        room = rooms[i % len(rooms)]
        day_offset = (i % 7) - 2
        hour = 9 + (i % 8)
        start_dt = (now + timedelta(days=day_offset)).replace(hour=hour, minute=0, second=0, microsecond=0)
        end_dt = start_dt + timedelta(hours=2)

        code = f"BKG-FAC-2026-{i+1:03d}"
        existing = db.query(RoomBooking).filter(RoomBooking.booking_code == code).first()
        if not existing:
            bkg = RoomBooking(
                id=str(uuid.uuid4()),
                booking_code=code,
                room_id=room.id,
                user_id=faculty.id,
                user_role="faculty",
                title=title,
                purpose=purpose,
                start_time=start_dt,
                end_time=end_dt,
                status="confirmed" if i % 12 != 0 else "cancelled",
                equipment_required=json.dumps(eq),
                created_at=now - timedelta(days=5 - (i % 4))
            )
            db.add(bkg)

    sample_reports = [
        ("Projector lamp failure in CS Seminar Hall", "The 4K ceiling projector shows red lamp error code and turns off after 5 minutes.", "classroom", "high", "in_progress"),
        ("Wi-Fi dead zone in Computer Lab B (Rows 3-5)", "Students cannot access GitHub during the programming practical session.", "network", "critical", "submitted"),
        ("Air Conditioning leaking water onto server rack", "AC unit 2 in Systems Lab is dripping condensation near the equipment rack.", "equipment", "critical", "in_progress"),
        ("Microphone wireless interference in Auditorium 1", "Audio pops loudly whenever handheld mic B is enabled during guest lecture.", "classroom", "medium", "resolved"),
        ("Additional power extensions required for CS Hackathon", "Need 8 surge-protected extension blocks delivered to ENG-204.", "electrical", "medium", "resolved"),
        ("Smartboard touch calibration drift in Classroom 102", "Stylus touches register 4 inches to the left of physical contact point.", "classroom", "low", "submitted"),
        ("Restroom door latch jammed near CS Faculty Lounge", "The main door latch on 2nd floor restroom requires immediate latch replacement.", "cleanliness", "medium", "resolved"),
        ("Lab PC workstation #14 Blue Screen on boot", "Workstation fails to load Windows 11 kernel; memory diagnostic error.", "equipment", "medium", "in_progress"),
        ("HDMI audio cutout from podium cable", "Audio works intermittently; copper pins inside HDMI jack are bent.", "classroom", "high", "resolved"),
        ("Emergency exit light flickering in ENG West Stairwell", "Fluorescent tube is constantly flickering creating a safety hazard.", "electrical", "low", "submitted"),
        ("Lab PCs require Python 3.12 SDK upgrade before exam", "Midterm exam requires PyTorch and JupyterLab packages installed on 40 PCs.", "software", "high", "in_progress"),
        ("Classroom window blind cord snapped in ENG-301", "Blinds cannot be lowered; sun glare reflects directly on main whiteboards.", "infrastructure", "low", "resolved"),
        ("Ethernet switch port 18 link flapping in Lab A", "Network drops every 90 seconds on switches rack unit 4.", "network", "critical", "in_progress"),
        ("Classroom lectern wheel broke while repositioning", "Right castor wheel snapped off lectern during class changeover.", "furniture", "medium", "submitted"),
    ]

    for i, (title, desc, cat, urg, status) in enumerate(sample_reports):
        code = f"RPT-FAC-2026-{i+1:03d}"
        existing = db.query(Report).filter(Report.report_code == code).first()
        if not existing:
            room = rooms[i % len(rooms)]
            rep = Report(
                id=str(uuid.uuid4()),
                report_code=code,
                title=title,
                description=desc,
                category=cat,
                urgency=urg,
                building_id=room.building_id,
                room_id=room.id,
                reporter_id=faculty.id,
                reporter_role="faculty",
                source="web_portal",
                status=status,
                ai_extracted_meta=json.dumps({
                    "category": cat,
                    "urgency": urg,
                    "location_room": room.name,
                    "confidence_score": 0.94
                }),
                created_at=now - timedelta(days=7 - (i % 6), hours=i)
            )
            db.add(rep)

    notices = [
        ("Pre-Exam Readiness Signoff Confirmed", "Computer Lab A has been inspected and certified for CS304 Midterm Exam today.", "success", "/faculty/exam-support"),
        ("Campus Scheduled Wi-Fi Upgrade Tonight", "Core gateway maintenance will occur from 23:00 to 01:00 across Engineering Block.", "warning", "/faculty/notices"),
        ("Urgent Notice: ENG-104 Air Conditioning Repaired", "Maintenance technician completed replacement of HVAC filter in ENG-104.", "info", "/faculty/timetable"),
        ("Midterm Examination Proctor Guidelines Issued", "Dean of Academic Affairs published updated examination proctor guidelines.", "info", "/faculty/notices"),
        ("Classroom AV Calibration Schedule Announced", "Facilities team will conduct audio/visual equipment calibration this Friday afternoon.", "info", "/faculty/notices"),
        ("Fire Drill & Building Evacuation Alert", "Annual scheduled fire safety inspection drill scheduled for 14:00 Tuesday.", "warning", "/faculty/notices"),
        ("New High-Performance Computing Cluster Access", "Computer Science faculty may now requisition GPU compute nodes for research.", "success", "/faculty/notices"),
        ("Lab PC Deep-Clean Completed", "Janitorial staff completed scheduled anti-static cleaning across Computer Labs A and B.", "info", "/faculty/notices")
    ]

    for i, (title, msg, n_type, link) in enumerate(notices):
        n_id = f"notif-fac-2026-{i+1:03d}"
        existing = db.query(Notification).filter(Notification.id == n_id).first()
        if not existing:
            notif = Notification(
                id=n_id,
                recipient_id=faculty.id,
                recipient_role="faculty",
                title=title,
                message=msg,
                type=n_type,
                read=i > 3,
                link_url=link,
                created_at=now - timedelta(hours=i * 6)
            )
            db.add(notif)

