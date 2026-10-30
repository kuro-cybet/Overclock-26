# CampusOps · Interactive Demonstration & Scenario Guide

This guide walks through the complete end-to-end operational story demonstrating how CampusOps functions as **one unified engine with four connected role experiences**.

---

## Scenario 1: Examination Room Unavailable & Automated Relocation

### Narrative
An examination (*CS304: Distributed Systems Midterm*) is scheduled in **Computer Lab A (ENG-101)** starting in 30 minutes. The room suffers a critical facility outage (HVAC failure / power issue).

### Step-by-Step Walkthrough
1. **Sign in as Admin** (`admin@campusops.edu`).
2. Navigate to **Scenario Simulator** (`/admin/simulator`).
3. Select the tab **Examination Room Unavailable** and click **Trigger Disruption**.
   - The room status switches to `unavailable`.
   - The Automated Recovery Engine assesses the dependency: CS304 Midterm Exam (60 students, required features: Wi-Fi, Lab PCs).
   - The engine searches all 60 campus rooms, verifies capacities, checks timetable schedule collisions, and surfaces top feasible alternatives (e.g. *Computer Lab B* or *Engineering Lecture Hall 1*).
4. Review the feasibility score and click **Execute Option**.
5. Switch persona to **Faculty** (`faculty@campusops.edu`):
   - Notice the targeted notification: *Exam Relocation Confirmed to Computer Lab B*.
   - Check the **Timetable** view: the exam slot has been updated cleanly.
6. Switch persona to **Student** (`student@campusops.edu`):
   - Notice the high-priority alert: *Exam Room Change Alert: CS304 has moved to Computer Lab B. Please report there.*

---

## Scenario 2: Multiple Wi-Fi Outage Complaints & Canonical Correlation

### Narrative
The main Cisco Access Point in Computer Lab A fails. Four students sitting in the lab submit complaints at the same time.

### Step-by-Step Walkthrough
1. Navigate to **Scenario Simulator** (`/admin/simulator`).
2. Select **Multiple Wi-Fi Complaints** and click **Trigger Disruption**.
3. 4 independent student reports are processed through the **AI Intake Service**:
   - Issue category extracted: `Network / Wi-Fi`.
   - Location extracted: `Engineering Block, Computer Lab A`.
   - Urgency flagged: `Critical (Upcoming Examination)`.
4. The **Incident Correlation Service** groups all 4 reports into one canonical incident (`INC-2026-XXXX`).
5. Open **Incidents & Triage** (`/admin/incidents`):
   - See the canonical incident with badge **4 Linked Reports**.
   - Inspect details: each original student complaint is preserved with reporter identity, timestamp, and metadata.
6. Targeted notifications are automatically queued in the **Notification Outbox** (`/api/v1/integrations/email/outbox`) notifying each student that their ticket has been merged and dispatched.

---

## Scenario 3: Technician Absence & Skill-Based Workload Reassignment

### Narrative
Technician David Miller (Network Specialist) calls in sick. A high-priority P1 work order is assigned to him.

### Step-by-Step Walkthrough
1. In the **Scenario Simulator**, choose **Technician Unavailable**.
2. Click **Trigger Disruption**:
   - David Miller's status is set to `absent`.
   - The Assignment Engine recalculates all 24 campus technicians.
   - Evaluates: Required Skills (`network`, `hardware`), Current Workload, and Morning Shift availability.
   - Automatically reassigns the work order to the top-scoring qualified replacement technician without breaching the SLA deadline.
3. Switch persona to **Technicians Portal**:
   - Log in as the replacement technician.
   - The work order appears on their active task queue with diagnostic checklist ready for execution.

---

## Scenario 4: Critical Part Out of Stock & Separation of Duties

### Narrative
A technician needs an Enterprise Wi-Fi 6 AP Module (`INV-NET-007`), but central stores have 0 available units.

### Step-by-Step Walkthrough
1. Trigger **Critical Part Out of Stock** in the Simulator.
2. The transactional inventory reservation fails with `HTTP 409 Conflict`.
3. The work order is cleanly flagged as **Blocked** with reason: *Required part unavailable in central store*. False completion is prevented.
4. An emergency procurement request is generated along with an approval request.
5. **Governance Safety Demonstration**:
   - Try to approve the purchase while logged in as Facilities Admin (the requester) -> **Blocked by Separation of Duties policy**.
   - Switch persona to **Procurement Approver** (`procurement@campusops.edu`).
   - Go to **Pending Approvals** (`/admin/approvals`) and approve the request.
   - The inventory stock is replenished and the work order unblocks automatically.

---

## Baseline Reset
At any point, click **Reset Baseline State** in the simulator or run `scripts\reset-database.bat` to restore pristine seed data.

