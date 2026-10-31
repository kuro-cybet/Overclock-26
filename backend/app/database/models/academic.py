import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from app.database.base import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_code = Column(String(50), nullable=False, unique=True, index=True)
    course_name = Column(String(150), nullable=False)
    department = Column(String(100), nullable=False, index=True)
    credits = Column(Integer, default=3, nullable=False)
    semester = Column(Integer, default=1, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class AcademicSection(Base):
    __tablename__ = "academic_sections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    section_name = Column(String(50), nullable=False, index=True)  # e.g., "A", "B", "CSE-A"
    department = Column(String(100), nullable=False, index=True)
    academic_year = Column(String(20), nullable=False, default="2026-2027")
    semester = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class TimetableSlot(Base):
    __tablename__ = "timetable_slots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    section_id = Column(String(36), nullable=False, index=True)
    course_id = Column(String(36), nullable=False, index=True)
    faculty_id = Column(String(36), nullable=False, index=True)
    room_id = Column(String(36), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False, index=True)  # 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday
    start_time = Column(String(10), nullable=False)  # HH:MM (e.g., "09:00")
    end_time = Column(String(10), nullable=False)    # HH:MM (e.g., "10:00")
    slot_type = Column(String(30), default="lecture", nullable=False)  # lecture, lab, tutorial, break
    is_published = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class StudentEnrollment(Base):
    __tablename__ = "student_enrollments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), nullable=False, index=True)
    section_id = Column(String(36), nullable=False, index=True)
    course_id = Column(String(36), nullable=False, index=True)
    academic_year = Column(String(20), nullable=False, default="2026-2027")
    semester = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class ClassSession(Base):
    __tablename__ = "class_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timetable_slot_id = Column(String(36), nullable=True, index=True)
    section_id = Column(String(36), nullable=False, index=True)
    course_id = Column(String(36), nullable=False, index=True)
    faculty_id = Column(String(36), nullable=False, index=True)
    room_id = Column(String(36), nullable=False, index=True)
    session_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    start_time = Column(String(10), nullable=False)  # HH:MM
    end_time = Column(String(10), nullable=False)    # HH:MM
    status = Column(String(30), default="completed", nullable=False)  # scheduled, completed, cancelled
    topic_covered = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), nullable=False, index=True)
    student_id = Column(String(36), nullable=False, index=True)
    status = Column(String(20), default="present", nullable=False)  # present, absent, late
    remarks = Column(String(255), nullable=True)
    marked_by_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class AttendanceCorrectionRequest(Base):
    __tablename__ = "attendance_correction_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), nullable=False, index=True)
    student_id = Column(String(36), nullable=False, index=True)
    current_status = Column(String(20), nullable=False)
    requested_status = Column(String(20), nullable=False)
    reason = Column(Text, nullable=False)
    requester_id = Column(String(36), nullable=False)  # faculty user id
    status = Column(String(20), default="pending", nullable=False)  # pending, approved, rejected
    decision_reason = Column(Text, nullable=True)
    decided_by_id = Column(String(36), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

