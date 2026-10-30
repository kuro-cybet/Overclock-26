# CampusOps · User Roles & Governance Matrix

CampusOps implements strict Role-Based Access Control (RBAC) with sub-role boundary separation.

---

## 1. Primary Portal Roles

| Portal Role | Design Accent | Purpose & Scope |
| :--- | :--- | :--- |
| **Admin** | `#F29877` (Coral) | Central campus operations command, incident correlation, asset oversight, work dispatch, scenario simulations, and analytics. |
| **Technicians** | `#287D70` (Teal) | Operational field desk, skill-matched work order execution, task checklists, parts requests, and daily room readiness sign-off. |
| **Faculty** | `#8EB9D8` (Blue) | Academic operations, lecture and exam timetables, room booking requests, and classroom support tickets. |
| **Students** | `#A58ACF` (Lavender) | Student self-service, quick incident reporting (Wi-Fi, classroom, hygiene), personal ticket tracking, and campus facility status. |

---

## 2. Admin Sub-Role Boundaries

As defined in Page 5 & 6 of the blueprint:

- **Department Manager (`dept_mgr@campusops.edu`)**:
  - Authorised operational oversight and cross-departmental coordination.
  - Grants final authorization on costly repairs and exam relocation room overrides.
- **Facilities Administrator (`facilities@campusops.edu`)**:
  - Manages rooms, assets, facilities, maintenance schedules, and daily readiness tracking.
  - Requisitions inventory replenishment parts.
- **Procurement Approver (`procurement@campusops.edu`)**:
  - Authorised to review and approve purchase and procurement requests within configured fiscal limits.
- **System Administrator (`admin@campusops.edu` / `sysadmin@campusops.edu`)**:
  - Controls users, roles, configurations, and core platform settings.
  - **Important Safety Rule**: Does **not** automatically receive business approval authority! Separation of duties is enforced at API route handlers.

---

## 3. Technician Sub-Role Boundaries

The portal adapts tasks and actions to the assigned technician sub-role, building/floor, shift, and permissions:

- **Floor Incharge (`floor_incharge@campusops.edu`)**:
  - Coordinates floor tasks and verifies daily room readiness status across their designated floor.
- **Maintenance Technician (`tech@campusops.edu` / `maintenance@campusops.edu`)**:
  - Diagnoses hardware failures, repairs electrical/network/HVAC assets, consumes parts, and uploads completion evidence.
- **Janitor (`janitor@campusops.edu`)**:
  - Handles sanitation, hygiene, waste management, and chemical cleanup requests.
- **Room Incharge (`room_incharge@campusops.edu`)**:
  - Conducts physical room checks (podium, projector, PC terminals) and signs off readiness before classes.

