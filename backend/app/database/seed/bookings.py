import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.models.booking import RoomBooking

def seed_bookings(db: Session, rooms, faculty_users):
    bookings = []
    now = datetime.utcnow()

    # Find Computer Lab A for key scenario
    comp_lab_a = next((r for r in rooms if "Computer Lab A" in r.name), rooms[0])
    faculty_lead = faculty_users[0]  # Prof Finch

    # 1. Critical upcoming examination booking in Computer Lab A (in 30 mins!)
    exam_booking = RoomBooking(
        booking_code="BKG-EXAM-2026-001",
        room_id=comp_lab_a.id,
        user_id=faculty_lead.id,
        user_role="faculty",
        title="CS304: Distributed Systems Midterm Examination",
        purpose="examination",
        start_time=now + timedelta(minutes=30),
        end_time=now + timedelta(minutes=150),
        status="confirmed",
        equipment_required=json.dumps(["wifi", "lab_pcs", "ac"])
    )
    db.add(exam_booking)
    bookings.append(exam_booking)

    # 2. Upcoming exam in ENG-104
    eng_104 = next((r for r in rooms if "104" in r.room_number and "ENG" in r.room_number), rooms[1])
    exam_booking_2 = RoomBooking(
        booking_code="BKG-EXAM-2026-002",
        room_id=eng_104.id,
        user_id=faculty_users[1].id,
        user_role="faculty",
        title="EE201: Electronic Circuits Final Assessment",
        purpose="examination",
        start_time=now + timedelta(hours=2),
        end_time=now + timedelta(hours=5),
        status="confirmed",
        equipment_required=json.dumps(["wifi", "projector", "sound_system"])
    )
    db.add(exam_booking_2)
    bookings.append(exam_booking_2)

    purposes = ["lecture", "lab_session", "examination", "meeting", "seminar"]
    course_titles = [
        "CS101 Introduction to Computing",
        "PH102 General Physics Lab",
        "CH201 Organic Chemistry Seminar",
        "EE305 Signal Processing",
        "ME204 Thermodynamics Workshop",
        "MATH105 Multivariable Calculus",
        "ENG301 Technical Writing",
        "AI401 Deep Learning Practical",
        "BIO202 Cellular Biology",
        "DS301 Data Mining Techniques"
    ]

    # Generate 78 more bookings across various dates/times to hit 80 total
    for i in range(2, 80):
        room = rooms[i % len(rooms)]
        faculty = faculty_users[i % len(faculty_users)]
        purpose = purposes[i % len(purposes)]
        course = course_titles[i % len(course_titles)]

        # Spread bookings across -3 days to +5 days
        day_offset = (i % 9) - 3
        hour_start = 8 + (i % 9)
        start_dt = (now + timedelta(days=day_offset)).replace(hour=hour_start, minute=0, second=0, microsecond=0)
        end_dt = start_dt + timedelta(hours=2)

        booking = RoomBooking(
            booking_code=f"BKG-2026-{i+1:04d}",
            room_id=room.id,
            user_id=faculty.id,
            user_role="faculty",
            title=f"{course} - Section {chr(65 + (i % 4))}",
            purpose=purpose,
            start_time=start_dt,
            end_time=end_dt,
            status="confirmed" if i % 15 != 0 else "cancelled",
            equipment_required=json.dumps(["wifi", "projector"])
        )
        db.add(booking)
        bookings.append(booking)

    db.flush()
    return bookings

