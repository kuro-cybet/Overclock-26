BEGIN;

UPDATE public.users
SET sub_role = 'all_skills_technician'
WHERE lower(email) = 'techtroveversion3@gmail.com'
  AND role = 'technician';

UPDATE public.technician_assignments
SET sub_role = 'all_skills_technician'
WHERE lower(email) = 'techtroveversion3@gmail.com';

UPDATE public.staff_profiles AS profile
SET skills = '["network","wifi","cabling","router_config","hardware","electrical","power_distribution","exam_setup","classroom_readiness","av_equipment","hvac","plumbing","water_systems","sanitary_maintenance","general_cleaning","sanitation","waste_management"]'
FROM public.users AS account
WHERE account.id = profile.user_id
  AND lower(account.email) = 'techtroveversion3@gmail.com'
  AND account.role = 'technician';

COMMIT;
