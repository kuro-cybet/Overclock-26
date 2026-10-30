# CampusOps · API Documentation

Base URL: `http://localhost:8000/api/v1`  
Interactive OpenAPI UI: `http://localhost:8000/docs`

---

## 1. Authentication & RBAC

### `POST /auth/login`
Authenticates a user against persistent database records and issues a 24-hour signed JWT bearer token.

> Password sign-in is **disabled by default** because CampusOps uses Google
> sign-in. It only works when the server is started with
> `PASSWORD_LOGIN_ENABLED=true`, and returns `403` otherwise.

**Request Body:**
```json
{
  "email": "rajesekersudharsan@gmail.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "u-admin-1",
    "email": "rajesekersudharsan@gmail.com",
    "name": "Rajesekar Sudharsan",
    "role": "admin",
    "sub_role": "system_admin"
  }
}
```

### `POST /auth/google`
Signs in with a Google Identity Services ID token. The server verifies the token
against `GOOGLE_CLIENT_ID`, requires a verified email, and reads the role
**only** from the corresponding role-specific allowlist table. The client
never sends a role.

```json
{
  "credential": "<google-id-token>"
}
```

* `401` — invalid/expired token, or unverified email
* `403` — Google account does not have exactly one active CampusOps role assignment
* `503` — Google sign-in is not configured on the server

### `GET /auth/me`
Retrieves current identity, permissions, and assigned building/floor scope. Requires `Authorization: Bearer <token>`.

---

## 2. Incident Intake & Correlation

### `POST /reports`
Submits a natural language issue report. Automatically passes through the AI Extraction Adapter to detect category, urgency, location, and potential duplicates.

### `POST /incidents/correlate`
Aggregates multiple individual user reports into a single canonical incident.
```json
{
  "report_ids": ["rpt-1", "rpt-2", "rpt-3"],
  "target_incident_id": null,
  "new_title": "Major Outage: Engineering Wi-Fi AP Offline"
}
```

---

## 3. Operations & Work Orders

### `GET /work-orders`
Lists work orders. When accessed by a technician, results are automatically scoped to their assigned tasks.

### `PATCH /work-orders/{id}`
Updates work order state, checklist progress, technician diagnosis notes, and evidence. Validates state machine rules.

### `POST /work-orders/{id}/reassign`
Reassigns work order within policy:
```json
{
  "new_technician_id": "tech-uuid",
  "reassignment_reason": "Absence coverage"
}
```

---

## 4. Timetable & Room Bookings

### `GET /bookings`
Lists university bookings with start/end timestamps and equipment requirements.

### `POST /bookings`
Books a room. Enforces collision detection, capacity validation, and feature matching. Returns `409 Conflict` if an overlap is detected.

---

## 5. Warehouse & Approvals

### `POST /inventory/reserve`
Transactionally reserves stock quantity for a work order. Blocks work order if available inventory is insufficient.

### `POST /approvals/{id}/decision`
Approve or reject a procurement, costly repair, or room override request. Strictly enforces separation of duties.

---

## 6. Disruption Recovery & Simulator

### `POST /recovery/plan`
Generates feasible alternatives, scoring capacity match, timetable clearance, and staff availability.

### `POST /recovery/execute`
Revalidates room availability, stock levels, and staff presence immediately before executing relocation or reassignment.

### `POST /simulations/{scenario}`
Triggers one of the 4 blueprint disruption scenarios:
- `exam_room_unavailable`
- `technician_unavailable`
- `stock_shortage`
- `wifi_outage`

### `POST /simulations/reset`
Restores the pristine university seed baseline without leaving orphaned records.
