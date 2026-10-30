BEGIN;

CREATE TABLE IF NOT EXISTS public.admin_assignments (
    id character varying(36) PRIMARY KEY,
    email character varying(255) NOT NULL UNIQUE,
    sub_role character varying(50),
    department character varying(100),
    building_id character varying(36),
    floor_id character varying(36),
    is_active boolean NOT NULL DEFAULT true,
    invited_by character varying(36),
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    consumed_at timestamp without time zone
);

CREATE TABLE IF NOT EXISTS public.technician_assignments (
    id character varying(36) PRIMARY KEY,
    email character varying(255) NOT NULL UNIQUE,
    sub_role character varying(50),
    department character varying(100),
    building_id character varying(36),
    floor_id character varying(36),
    is_active boolean NOT NULL DEFAULT true,
    invited_by character varying(36),
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    consumed_at timestamp without time zone
);

CREATE TABLE IF NOT EXISTS public.faculty_assignments (
    id character varying(36) PRIMARY KEY,
    email character varying(255) NOT NULL UNIQUE,
    sub_role character varying(50),
    department character varying(100),
    building_id character varying(36),
    floor_id character varying(36),
    is_active boolean NOT NULL DEFAULT true,
    invited_by character varying(36),
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    consumed_at timestamp without time zone
);

CREATE TABLE IF NOT EXISTS public.student_assignments (
    id character varying(36) PRIMARY KEY,
    email character varying(255) NOT NULL UNIQUE,
    sub_role character varying(50),
    department character varying(100),
    building_id character varying(36),
    floor_id character varying(36),
    is_active boolean NOT NULL DEFAULT true,
    invited_by character varying(36),
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    consumed_at timestamp without time zone
);

DO $$
BEGIN
    IF to_regclass('public.role_assignments') IS NULL THEN
        RAISE EXCEPTION 'Expected public.role_assignments to exist; refusing to migrate.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM public.role_assignments
        WHERE role NOT IN ('admin', 'technician', 'faculty', 'student')
    ) THEN
        RAISE EXCEPTION 'role_assignments contains an unsupported role; resolve it before migration.';
    END IF;

    IF EXISTS (
        SELECT email
        FROM public.role_assignments
        GROUP BY email
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION 'role_assignments contains duplicate emails; resolve them before migration.';
    END IF;
END
$$;

INSERT INTO public.admin_assignments
    (id, email, sub_role, department, building_id, floor_id, is_active, invited_by, created_at, consumed_at)
SELECT id, email, sub_role, department, building_id, floor_id, is_active, invited_by, created_at, consumed_at
FROM public.role_assignments
WHERE role = 'admin'
ON CONFLICT (email) DO UPDATE SET
    sub_role = EXCLUDED.sub_role,
    department = EXCLUDED.department,
    building_id = EXCLUDED.building_id,
    floor_id = EXCLUDED.floor_id,
    is_active = EXCLUDED.is_active,
    invited_by = EXCLUDED.invited_by,
    created_at = EXCLUDED.created_at,
    consumed_at = EXCLUDED.consumed_at;

INSERT INTO public.technician_assignments
    (id, email, sub_role, department, building_id, floor_id, is_active, invited_by, created_at, consumed_at)
SELECT id, email, sub_role, department, building_id, floor_id, is_active, invited_by, created_at, consumed_at
FROM public.role_assignments
WHERE role = 'technician'
ON CONFLICT (email) DO UPDATE SET
    sub_role = EXCLUDED.sub_role,
    department = EXCLUDED.department,
    building_id = EXCLUDED.building_id,
    floor_id = EXCLUDED.floor_id,
    is_active = EXCLUDED.is_active,
    invited_by = EXCLUDED.invited_by,
    created_at = EXCLUDED.created_at,
    consumed_at = EXCLUDED.consumed_at;

INSERT INTO public.faculty_assignments
    (id, email, sub_role, department, building_id, floor_id, is_active, invited_by, created_at, consumed_at)
SELECT id, email, sub_role, department, building_id, floor_id, is_active, invited_by, created_at, consumed_at
FROM public.role_assignments
WHERE role = 'faculty'
ON CONFLICT (email) DO UPDATE SET
    sub_role = EXCLUDED.sub_role,
    department = EXCLUDED.department,
    building_id = EXCLUDED.building_id,
    floor_id = EXCLUDED.floor_id,
    is_active = EXCLUDED.is_active,
    invited_by = EXCLUDED.invited_by,
    created_at = EXCLUDED.created_at,
    consumed_at = EXCLUDED.consumed_at;

INSERT INTO public.student_assignments
    (id, email, sub_role, department, building_id, floor_id, is_active, invited_by, created_at, consumed_at)
SELECT id, email, sub_role, department, building_id, floor_id, is_active, invited_by, created_at, consumed_at
FROM public.role_assignments
WHERE role = 'student'
ON CONFLICT (email) DO UPDATE SET
    sub_role = EXCLUDED.sub_role,
    department = EXCLUDED.department,
    building_id = EXCLUDED.building_id,
    floor_id = EXCLUDED.floor_id,
    is_active = EXCLUDED.is_active,
    invited_by = EXCLUDED.invited_by,
    created_at = EXCLUDED.created_at,
    consumed_at = EXCLUDED.consumed_at;

DO $$
BEGIN
    IF EXISTS (
        SELECT email
        FROM (
            SELECT email FROM public.admin_assignments WHERE is_active
            UNION ALL
            SELECT email FROM public.technician_assignments WHERE is_active
            UNION ALL
            SELECT email FROM public.faculty_assignments WHERE is_active
            UNION ALL
            SELECT email FROM public.student_assignments WHERE is_active
        ) active_assignments
        GROUP BY email
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION 'An email has multiple active role assignments; resolve duplicates before deploying Google sign-in.';
    END IF;
END
$$;

ALTER TABLE public.admin_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.technician_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.faculty_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_assignments ENABLE ROW LEVEL SECURITY;

REVOKE ALL PRIVILEGES ON TABLE
    public.admin_assignments,
    public.technician_assignments,
    public.faculty_assignments,
    public.student_assignments
FROM anon, authenticated;

COMMIT;

-- Keep public.role_assignments until the updated backend is deployed and sign-in
-- is verified. It can then be removed with:
-- DROP TABLE public.role_assignments;
