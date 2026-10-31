-- =============================================================================
-- CampusOps — Migration: Academic Timetable, Attendance & Chennai Transport
-- Migration File: 20261031050000_academic_and_transport_system.sql
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- 1. Academic Courses
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.courses (
    id character varying(36) PRIMARY KEY,
    course_code character varying(50) NOT NULL,
    course_name character varying(150) NOT NULL,
    department character varying(100) NOT NULL,
    credits integer NOT NULL DEFAULT 3,
    semester integer NOT NULL DEFAULT 1,
    description text,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamp without time zone NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_courses_code ON public.courses (course_code);
CREATE INDEX IF NOT EXISTS idx_courses_dept ON public.courses (department);

-- -----------------------------------------------------------------------------
-- 2. Academic Sections
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.academic_sections (
    id character varying(36) PRIMARY KEY,
    section_name character varying(50) NOT NULL,
    department character varying(100) NOT NULL,
    academic_year character varying(20) NOT NULL DEFAULT '2026-2027',
    semester integer NOT NULL DEFAULT 1,
    created_at timestamp without time zone NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_academic_sections_dept ON public.academic_sections (department);

-- -----------------------------------------------------------------------------
-- 3. Timetable Slots
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.timetable_slots (
    id character varying(36) PRIMARY KEY,
    section_id character varying(36) NOT NULL,
    course_id character varying(36) NOT NULL,
    faculty_id character varying(36) NOT NULL,
    room_id character varying(36) NOT NULL,
    day_of_week integer NOT NULL, -- 0=Monday ... 5=Saturday
    start_time character varying(10) NOT NULL,
    end_time character varying(10) NOT NULL,
    slot_type character varying(30) NOT NULL DEFAULT 'lecture',
    is_published boolean NOT NULL DEFAULT true,
    created_at timestamp without time zone NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at timestamp without time zone NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_timetable_slots_sec ON public.timetable_slots (section_id);
CREATE INDEX IF NOT EXISTS idx_timetable_slots_fac ON public.timetable_slots (faculty_id);
CREATE INDEX IF NOT EXISTS idx_timetable_slots_room ON public.timetable_slots (room_id);
CREATE INDEX IF NOT EXISTS idx_timetable_slots_day ON public.timetable_slots (day_of_week);

-- -----------------------------------------------------------------------------
-- 4. Student Enrollments
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.student_enrollments (
    id character varying(36) PRIMARY KEY,
    student_id character varying(36) NOT NULL,
    section_id character varying(36) NOT NULL,
    course_id character varying(36) NOT NULL,
    academic_year character varying(20) NOT NULL DEFAULT '2026-2027',
    semester integer NOT NULL DEFAULT 1,
    created_at timestamp without time zone NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_student_enrollments_student ON public.student_enrollments (student_id);
CREATE INDEX IF NOT EXISTS idx_student_enrollments_section ON public.student_enrollments (section_id);

-- -----------------------------------------------------------------------------
-- 5. Class Sessions
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.class_sessions (
    id character varying(36) PRIMARY KEY,
    timetable_slot_id character varying(36),
    section_id character varying(36) NOT NULL,
    course_id character varying(36) NOT NULL,
    faculty_id character varying(36) NOT NULL,
    room_id character varying(36) NOT NULL,
    session_date character varying(10) NOT NULL, -- YYYY-MM-DD
    start_time character varying(10) NOT NULL,
    end_time character varying(10) NOT NULL,
    status character varying(30) NOT NULL DEFAULT 'completed',
    topic_covered text,
    created_at timestamp without time zone NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_class_sessions_date ON public.class_sessions (session_date);
CREATE INDEX IF NOT EXISTS idx_class_sessions_fac ON public.class_sessions (faculty_id);
CREATE INDEX IF NOT EXISTS idx_class_sessions_sec ON public.class_sessions (section_id);

-- -----------------------------------------------------------------------------
-- 6. Attendance Records
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.attendance_records (
    id character varying(36) PRIMARY KEY,
    session_id character varying(36) NOT NULL,
    student_id character varying(36) NOT NULL,
    status character varying(20) NOT NULL DEFAULT 'present',
    remarks character varying(255),
    marked_by_id character varying(36) NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at timestamp without time zone NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_att_records_session ON public.attendance_records (session_id);
CREATE INDEX IF NOT EXISTS idx_att_records_student ON public.attendance_records (student_id);

-- -----------------------------------------------------------------------------
-- 7. Attendance Correction Requests
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.attendance_correction_requests (
    id character varying(36) PRIMARY KEY,
    session_id character varying(36) NOT NULL,
    student_id character varying(36) NOT NULL,
    current_status character varying(20) NOT NULL,
    requested_status character varying(20) NOT NULL,
    reason text NOT NULL,
    requester_id character varying(36) NOT NULL,
    status character varying(20) NOT NULL DEFAULT 'pending',
    decision_reason text,
    decided_by_id character varying(36),
    decided_at timestamp without time zone,
    created_at timestamp without time zone NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_att_corr_session ON public.attendance_correction_requests (session_id);
CREATE INDEX IF NOT EXISTS idx_att_corr_status ON public.attendance_correction_requests (status);

-- -----------------------------------------------------------------------------
-- 8. Chennai Campus Transport Routes
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.transport_routes (
    id character varying(36) PRIMARY KEY,
    route_number character varying(50) NOT NULL,
    route_name character varying(150) NOT NULL,
    origin character varying(100) NOT NULL,
    destination character varying(100) NOT NULL DEFAULT 'Campus Main Gate',
    vehicle_number character varying(50) NOT NULL,
    driver_name character varying(100) NOT NULL,
    driver_phone character varying(30) NOT NULL,
    capacity integer NOT NULL DEFAULT 50,
    operating_days character varying(50) NOT NULL DEFAULT 'Mon-Sat',
    status character varying(30) NOT NULL DEFAULT 'active',
    announcement text,
    is_published boolean NOT NULL DEFAULT true,
    created_at timestamp without time zone NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_transport_routes_num ON public.transport_routes (route_number);

-- -----------------------------------------------------------------------------
-- 9. Transport Stops
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.transport_stops (
    id character varying(36) PRIMARY KEY,
    route_id character varying(36) NOT NULL,
    stop_name character varying(100) NOT NULL,
    sequence_order integer NOT NULL DEFAULT 1,
    pickup_time character varying(20) NOT NULL,
    drop_time character varying(20) NOT NULL,
    landmark character varying(150),
    created_at timestamp without time zone NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_transport_stops_route ON public.transport_stops (route_id);

-- -----------------------------------------------------------------------------
-- 10. Transport Allocations
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.transport_allocations (
    id character varying(36) PRIMARY KEY,
    user_id character varying(36) NOT NULL,
    route_id character varying(36) NOT NULL,
    stop_id character varying(36) NOT NULL,
    academic_year character varying(20) NOT NULL DEFAULT '2026-2027',
    status character varying(20) NOT NULL DEFAULT 'active',
    fee_status character varying(20) NOT NULL DEFAULT 'paid',
    created_at timestamp without time zone NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_transport_alloc_user ON public.transport_allocations (user_id);
CREATE INDEX IF NOT EXISTS idx_transport_alloc_route ON public.transport_allocations (route_id);

-- -----------------------------------------------------------------------------
-- 11. Transport Announcements
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.transport_announcements (
    id character varying(36) PRIMARY KEY,
    route_id character varying(36),
    title character varying(255) NOT NULL,
    message text NOT NULL,
    priority character varying(20) NOT NULL DEFAULT 'normal',
    created_at timestamp without time zone NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_transport_announcements_route ON public.transport_announcements (route_id);

-- -----------------------------------------------------------------------------
-- 12. Enable Row Level Security & Lock Down Direct Anon Access
-- -----------------------------------------------------------------------------
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.academic_sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.timetable_slots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.class_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attendance_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attendance_correction_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transport_routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transport_stops ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transport_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transport_announcements ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.courses FROM anon;
REVOKE ALL ON public.academic_sections FROM anon;
REVOKE ALL ON public.timetable_slots FROM anon;
REVOKE ALL ON public.student_enrollments FROM anon;
REVOKE ALL ON public.class_sessions FROM anon;
REVOKE ALL ON public.attendance_records FROM anon;
REVOKE ALL ON public.attendance_correction_requests FROM anon;
REVOKE ALL ON public.transport_routes FROM anon;
REVOKE ALL ON public.transport_stops FROM anon;
REVOKE ALL ON public.transport_allocations FROM anon;
REVOKE ALL ON public.transport_announcements FROM anon;

COMMIT;

