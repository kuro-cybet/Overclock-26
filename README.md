# CAMPUSOPS
### Unified Multi-Portal University Operations & Disruption Management Platform

> Built to the exact specifications of the **CampusOps Development Blueprint** and **Four-Portal Integrated Functional Specification (Version 1.1)**.

---

## 🏛️ Project Objective & Principles

CampusOps delivers one integrated platform with four role-specific experiences, a shared persistent database, and an operational workflow engine that supports real state changes. 

Instead of four disconnected mockup dashboards:
- A **student** reports a Wi-Fi or lab fault in natural language.
- The **AI Intake Service** extracts entities (category, urgency, location, assets).
- **Faculty** sees the immediate academic impact on upcoming lecture/exam timetables.
- The **Admin Operations Centre** coordinates automated recovery and SLA tracking.
- A **technician** receives the skill-matched work order to complete physical repairs with checklist and evidence verification.

---

## 🎨 Design Direction: Creative Learning (Peach + Blue)

The user interface implements the exact design tokens and role accents specified in the blueprint:

| Token | Hex | Usage |
| :--- | :--- | :--- |
| **Warm Ivory** | `#FFF4E9` | Page backgrounds and warm surfaces |
| **Peach** | `#FFD6BA` | Selected navigation, soft emphasis, panels |
| **Coral** | `#F29877` | Admin accent and secondary actions |
| **Blue** | `#8EB9D8` | Faculty accent and informational elements |
| **Deep Blue** | `#345873` | Sidebar, primary buttons, and headings |

### Role Accent Matrix
- **Admin**: `#F29877` — Coral
- **Technicians**: `#287D70` — Teal
- **Faculty**: `#8EB9D8` — Blue
- **Students**: `#A58ACF` — Lavender

---

## 🚀 Quick Startup Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Automated Installation
Run the setup batch script:
```cmd
scripts\setup.bat
```
*(This creates `backend\venv`, installs Python requirements, and installs frontend node modules).*

### 2. Seed Database
Seed the coherent synthetic university dataset:
```cmd
scripts\seed-database.bat
```

### 3. Launch System
Start both the FastAPI backend (port 8000) and the Vite frontend (port 5173):
```cmd
scripts\start.bat
```
Open **http://localhost:5173** in your browser.

---

## 🔑 Demo Access & One-Click Persona Switching

All accounts use the password: `password123`

The login page features **One-Click Persona buttons** to jump instantly into any portal:

- **Admin Portal**: `admin@campusops.edu` (Dr. Sarah Mitchell, System Admin)
- **Department Manager**: `dept_mgr@campusops.edu` (Prof. Arthur Pendelton)
- **Facilities Admin**: `facilities@campusops.edu` (Elena Rostova)
- **Procurement Approver**: `procurement@campusops.edu` (Marcus Sterling)
- **Technicians Portal**: `tech@campusops.edu` (David Miller, Maintenance Tech)
- **Floor Incharge**: `floor_incharge@campusops.edu` (Maria Santos)
- **Faculty Portal**: `faculty@campusops.edu` (Prof. Alistair Finch)
- **Students Portal**: `student@campusops.edu` (Jordan Lee)

---

## 🔬 Disruption Scenario Simulator (Admin Portal)

Navigate to **`/admin/simulator`** in the Admin Portal to run all 4 blueprint scenarios:

1. **Examination Room Unavailable**: Marks exam room unavailable shortly before an exam; inspects dependencies, checks timetable conflicts across all 60 campus rooms, proposes scored feasible alternative rooms, and dispatches targeted student/faculty notifications.
2. **Technician Unavailable**: Marks assigned technician absent; recalculates eligible staff using skill matrices, workload balancing, and shifts; reassigns within policy.
3. **Critical Part Out of Stock**: Attempts reservation when stock is 0; work order blocks safely without false completion; auto-generates procurement and approval requests.
4. **Multiple Wi-Fi Complaints**: Submits multiple student complaints for one outage; runs AI correlation into one canonical incident while preserving individual complaint records.

To reset back to baseline at any time, click **Reset Baseline State** or run `scripts\reset-database.bat`.

---

## 🧪 Automated Test Suite

Both backend business rules and frontend design tokens are verified by automated test suites:

### Run Backend Pytest Suite (19 Tests Passing):
```cmd
cd backend
.\venv\Scripts\pytest
```
*Tests coverage: `test_auth.py`, `test_permissions.py`, `test_incidents.py`, `test_bookings.py`, `test_inventory.py`, `test_approvals.py`, `test_idempotency.py`, `test_simulations.py`.*

### Run Frontend Vitest Suite:
```cmd
cd frontend
npx vitest run
```

---

## 📧 Gmail Notifications (Google OAuth)

CampusOps delivers notification email through the `send-campusops-email` Supabase
Edge Function, which uses a Google OAuth 2.0 refresh token to call the Gmail API.
The FastAPI backend signs each queued message with HMAC-SHA256 and posts it to the
function — Google credentials never live in the backend.

Setup is a one-time, three-step flow:

```cmd
:: 1. Create an OAuth client (Desktop app) in Google Cloud and enable the Gmail API
:: 2. Generate the refresh token
python scripts\google_oauth_setup.py

:: 3. Store GOOGLE_* + CAMPUSOPS_WEBHOOK_SECRET as Supabase secrets, deploy, then
::    copy the same secret into backend\.env
supabase functions deploy send-campusops-email --no-verify-jwt
```

Until credentials are configured, outbox delivery is simulated so local
development and tests keep working. Set `CAMPUSOPS_ALWAYS_CC` (or reuse
`CAMPUSOPS_TEST_RECIPIENT`) to CC a demo inbox on every notification while the
real recipient stays in `To:`. The integration email endpoints are protected: the
inbox webhook needs a system-admin bearer token or a valid HMAC signature
(`CAMPUSOPS_INBOUND_SECRET`, falling back to `CAMPUSOPS_WEBHOOK_SECRET`), and the
outbox listing requires a system admin. Full walkthrough and troubleshooting:
[`documentation/gmail-oauth-setup.md`](documentation/gmail-oauth-setup.md).

---

## 📁 Repository Deliverable Structure

```text
CampusOps/
├── frontend/
│   ├── public/
│   │   ├── images/
│   │   ├── illustrations/
│   │   └── campus-logo.svg
│   ├── src/
│   │   ├── app/ (App.tsx, main.tsx, router.tsx, providers.tsx, query-client.ts)
│   │   ├── core/
│   │   │   ├── auth/ (AuthProvider, ProtectedRoute, RoleGuard)
│   │   │   ├── api/ (client.ts)
│   │   │   └── hooks/
│   │   ├── portals/ (admin/, technician/, faculty/, student/)
│   │   ├── features/ (incident-intake/, ai-processing/, recovery-engine/, etc.)
│   │   ├── shared/ (components/, forms/, charts/, layouts/)
│   │   ├── design-system/ (tokens.ts)
│   │   ├── types/
│   │   └── styles/ (index.css)
│   ├── tests/
│   ├── package.json
│   └── vite.config.ts
├── backend/
│   ├── venv/ (virtual environment)
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/ (v1 routes: auth, incidents, work_orders, rooms, inventory, recovery, etc.)
│   │   ├── core/ (security, permissions, state_machine, exceptions)
│   │   ├── database/ (connection, models/, seed/)
│   │   ├── schemas/
│   │   ├── services/ (intake, ai, correlation, assignment, booking, inventory, approval, recovery, sla)
│   │   ├── integrations/ (simulated_email, notification_adapter, webhook_simulator)
│   │   ├── simulations/ (exam_room, technician_absence, stock_shortage, wifi_outage)
│   │   └── tests/ (all 8 test files from plan)
│   ├── data/ (campusops.db)
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
├── documentation/
│   ├── architecture.md
│   ├── api-documentation.md
│   ├── database-schema.md
│   └── user-roles.md
├── demo/
│   ├── scenario-guide.md
│   └── demo-credentials.md
├── scripts/
│   ├── setup.bat
│   ├── start.bat
│   ├── reset-database.bat
│   └── seed-database.bat
├── .gitignore
└── README.md
```

