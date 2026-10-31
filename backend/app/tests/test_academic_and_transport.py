import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.database.connection import SessionLocal
from app.database.models.user import User
from app.database.models.room import Room
from app.database.models.academic import Course, AcademicSection, TimetableSlot, ClassSession, AttendanceRecord
from app.database.models.transport import TransportRoute, TransportStop
from app.services.academic_service import AcademicService
from app.services.transport_service import TransportService

client = TestClient(app)

def _get_auth_header(user: User) -> dict:
    from app.core.security import create_access_token
    token = create_access_token(subject=user.id, role=user.role, sub_role=user.sub_role)
    return {"Authorization": f"Bearer {token}"}

def test_academic_timetable_personal_access():
    db = SessionLocal()
    try:
        AcademicService.seed_default_academic_data(db)
        faculty = db.query(User).filter(User.role == "faculty").first()
        student = db.query(User).filter(User.role == "student").first()

        assert faculty is not None
        assert student is not None

        # 1. Faculty access
        fac_headers = _get_auth_header(faculty)
        fac_res = client.get("/api/v1/academic/timetable/my", headers=fac_headers)
        assert fac_res.status_code == 200
        fac_data = fac_res.json()
        assert "weekly_schedule" in fac_data
        assert "today_classes" in fac_data
        assert fac_data["faculty_id"] == faculty.id

        # 2. Student access
        stu_headers = _get_auth_header(student)
        stu_res = client.get("/api/v1/academic/timetable/my", headers=stu_headers)
        assert stu_res.status_code == 200
        stu_data = stu_res.json()
        assert "weekly_schedule" in stu_data
        assert "today_classes" in stu_data
        assert stu_data["student_id"] == student.id
    finally:
        db.close()

def test_timetable_conflict_detection():
    db = SessionLocal()
    try:
        AcademicService.seed_default_academic_data(db)
        admin = db.query(User).filter(User.role == "admin").first()
        faculty = db.query(User).filter(User.role == "faculty").first()
        room = db.query(Room).first()
        course = db.query(Course).first()
        section = db.query(AcademicSection).first()

        admin_headers = _get_auth_header(admin)

        # 1. First slot on Friday (Day 4) from 14:00 to 15:00
        slot1_payload = {
            "section_id": section.id,
            "course_id": course.id,
            "faculty_id": faculty.id,
            "room_id": room.id,
            "day_of_week": 4,
            "start_time": "14:00",
            "end_time": "15:00",
            "slot_type": "lecture",
            "is_published": True
        }
        res1 = client.post("/api/v1/academic/timetable", json=slot1_payload, headers=admin_headers)
        assert res1.status_code == 200
        assert res1.json()["status"] == "success"

        # 2. Conflicting slot: same faculty at overlapping time (14:30 to 15:30)
        slot2_payload = {
            "section_id": section.id,
            "course_id": course.id,
            "faculty_id": faculty.id,
            "room_id": room.id,
            "day_of_week": 4,
            "start_time": "14:30",
            "end_time": "15:30",
            "slot_type": "lab",
            "is_published": True
        }
        res2 = client.post("/api/v1/academic/timetable", json=slot2_payload, headers=admin_headers)
        assert res2.status_code == 400
        assert "Conflict" in res2.json()["detail"]

        # 3. Invalid time slot (start >= end)
        invalid_payload = {
            "section_id": section.id,
            "course_id": course.id,
            "faculty_id": faculty.id,
            "room_id": room.id,
            "day_of_week": 4,
            "start_time": "16:00",
            "end_time": "15:00",
            "slot_type": "lecture",
            "is_published": True
        }
        res3 = client.post("/api/v1/academic/timetable", json=invalid_payload, headers=admin_headers)
        assert res3.status_code == 400
        assert "Invalid time interval" in res3.json()["detail"]
    finally:
        db.close()

def test_non_admin_cannot_modify_timetable():
    db = SessionLocal()
    try:
        AcademicService.seed_default_academic_data(db)
        faculty = db.query(User).filter(User.role == "faculty").first()
        student = db.query(User).filter(User.role == "student").first()
        room = db.query(Room).first()
        course = db.query(Course).first()
        section = db.query(AcademicSection).first()

        payload = {
            "section_id": section.id,
            "course_id": course.id,
            "faculty_id": faculty.id,
            "room_id": room.id,
            "day_of_week": 1,
            "start_time": "16:00",
            "end_time": "17:00",
            "slot_type": "lecture",
            "is_published": True
        }

        # Faculty blocked
        fac_headers = _get_auth_header(faculty)
        res_fac = client.post("/api/v1/academic/timetable", json=payload, headers=fac_headers)
        assert res_fac.status_code == 403

        # Student blocked
        stu_headers = _get_auth_header(student)
        res_stu = client.post("/api/v1/academic/timetable", json=payload, headers=stu_headers)
        assert res_stu.status_code == 403
    finally:
        db.close()

def test_attendance_marking_and_shortage_calculation():
    db = SessionLocal()
    try:
        AcademicService.seed_default_academic_data(db)
        faculty = db.query(User).filter(User.role == "faculty").first()
        student = db.query(User).filter(User.role == "student").first()
        course = db.query(Course).first()
        section = db.query(AcademicSection).first()

        fac_headers = _get_auth_header(faculty)
        stu_headers = _get_auth_header(student)

        # 1. Faculty submits attendance
        submit_payload = {
            "section_id": section.id,
            "course_id": course.id,
            "session_date": "2026-10-31",
            "start_time": "09:00",
            "end_time": "10:00",
            "topic_covered": "Binary Search Trees",
            "records": [
                {"student_id": student.id, "status": "present", "remarks": "On-time arrival"}
            ]
        }
        sub_res = client.post("/api/v1/academic/attendance/submit", json=submit_payload, headers=fac_headers)
        assert sub_res.status_code == 200
        assert sub_res.json()["status"] == "success"
        assert sub_res.json()["present_count"] == 1

        # 2. Student retrieves attendance breakdown
        att_res = client.get("/api/v1/academic/attendance/my", headers=stu_headers)
        assert att_res.status_code == 200
        att_data = att_res.json()
        assert "courses" in att_data
        assert "overall_percentage" in att_data
        assert att_data["threshold"] == 75.0
        assert isinstance(att_data["has_overall_shortage"], bool)

        # 3. Student cannot mark attendance
        stu_submit = client.post("/api/v1/academic/attendance/submit", json=submit_payload, headers=stu_headers)
        assert stu_submit.status_code == 403
    finally:
        db.close()

def test_chennai_transport_routes_and_search():
    db = SessionLocal()
    try:
        TransportService.seed_default_routes(db)
        student = db.query(User).filter(User.role == "student").first()
        stu_headers = _get_auth_header(student)

        # 1. Get all routes
        res = client.get("/api/v1/transport/routes", headers=stu_headers)
        assert res.status_code == 200
        routes = res.json()
        assert len(routes) >= 5

        route_numbers = [r["route_number"] for r in routes]
        assert "RT-01" in route_numbers
        assert "RT-02" in route_numbers
        assert "RT-03" in route_numbers
        assert "RT-04" in route_numbers
        assert "RT-05" in route_numbers

        # Verify sequential stops for RT-01 (Tambaram)
        rt01 = next(r for r in routes if r["route_number"] == "RT-01")
        assert "Tambaram" in rt01["route_name"]
        stops = rt01["stops"]
        assert len(stops) >= 4
        stop_names = [s["stop_name"] for s in stops]
        assert any("Tambaram" in name for name in stop_names)
        assert any("Chromepet" in name for name in stop_names)
        assert any("Guindy" in name for name in stop_names)

        # 2. Search Chennai routes by area
        search_res = client.get("/api/v1/transport/routes?search=Velachery", headers=stu_headers)
        assert search_res.status_code == 200
        search_data = search_res.json()
        assert len(search_data) >= 1
        assert "Velachery" in search_data[0]["route_name"] or "Velachery" in search_data[0]["origin"]

        # 3. User allocation
        alloc_res = client.get("/api/v1/transport/my-assignment", headers=stu_headers)
        assert alloc_res.status_code == 200
        alloc_data = alloc_res.json()
        assert alloc_data["assigned"] is True
        assert "route" in alloc_data["allocation"]
        assert "stop" in alloc_data["allocation"]
    finally:
        db.close()
