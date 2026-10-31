# CampusOps — SPA Routing Fix & Portal UI Cleanup Report

**Date:** October 31, 2026  
**Repository:** `S:\Overclock-26`  
**Branch:** `main`  
**Status:** Successfully Implemented & Verified Locally

---

## 1. Root Cause Analysis: Production Reload & Navigation 404

### The Problem
When navigating within the CampusOps web application, React Router (`createBrowserRouter`) intercepts link clicks client-side via the HTML5 History API (`pushState`). However, when users:
- Hard refresh a page (e.g., `Ctrl + R` on `https://overclock-26.onrender.com/admin/incidents`),
- Open a deep URL directly in a new tab, or
- Use browser forward/backward buttons on un-cached routes,

the browser issues a direct HTTP `GET` request to Render's CDN/web server for `/admin/incidents`. Because Render's static site host searches the file system for a physical file named `admin/incidents` (which does not exist), the server responds with:

```http
HTTP/1.1 404 Not Found
Content-Type: text/plain; charset=utf-8
Server: cloudflare / Render
```

Empirical live verification on `https://overclock-26.onrender.com`:
- `curl.exe -I https://overclock-26.onrender.com` -> `HTTP/1.1 200 OK`
- `curl.exe -I https://overclock-26.onrender.com/login` -> `HTTP/1.1 404 Not Found`
- `curl.exe -I https://overclock-26.onrender.com/admin` -> `HTTP/1.1 404 Not Found`

---

## 2. Exact Routing Fix Implemented

### A. Infrastructure-as-Code: Render Static Site Rewrite Rule (`render.yaml`)
Created `render.yaml` at the repository root configuring the official Render static site blueprint with a wildcard SPA rewrite:

```yaml
services:
  - type: web
    name: overclock-26
    runtime: static
    rootDir: frontend
    buildCommand: npm run build
    staticPublishPath: dist
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
```

*How it works:* Render evaluates incoming requests against physical assets first (CSS, JS, SVG, images). If no static file matches the URL path, Render rewrites the request internally to `/index.html` with HTTP 200 without changing the browser URL. React Router then mounts and renders the matched route.

### B. Static Hosting Safeguards
- Created `frontend/public/_redirects`:
  ```
  /*    /index.html   200
  ```
  This is copied automatically into `dist/` on build and serves as a native fallback for standard static hosting providers.
- Created `frontend/static.json` for static server buildpacks.

### C. Application 404 & Routing Resilience (`router.tsx` & `NotFoundPage.tsx`)
- Created `frontend/src/shared/components/NotFoundPage.tsx`: A dedicated, responsive 404 view styled according to the CampusOps design system. It presents a clean message, a "Go Back" button (`navigate(-1)`), and a smart "Return to Dashboard" / "Go to Login" button based on active auth state.
- In `frontend/src/app/router.tsx`:
  - Replaced the silent catch-all redirect (`path: '*' -> <Navigate to="/login" />`) with `<NotFoundPage />`. Genuinely invalid URLs now clearly render the 404 page rather than bouncing authenticated users to login.
  - Added route `path: 'simulator'` in addition to `path: 'simulations'` under the Admin portal so that both `/admin/simulator` (referenced in the sidebar) and `/admin/simulations` route cleanly to `<ScenarioSimulatorView />`.
  - API requests remain unaffected since API communication routes directly to the separate backend service (`https://campusops-u6yt.onrender.com/api/v1`).

---

## 3. Removal of "ACTIVE PORTAL" Sidebar Section Across All 4 Roles

### File Modified
`frontend/src/shared/components/Sidebar.tsx`

### Implementation
- Permanently removed the entire Active Portal container:
  - The `"ACTIVE PORTAL"` section title.
  - The role badge (`ADMIN`, `TECHNICIAN`, `FACULTY`, `STUDENT`).
  - The role display name / department line (`system admin`, `facilities_admin`, etc.).
- Removed the unused `tokens` import and `currentAccent` variable.
- Reclaimed vertical space so the portal navigation items (`<nav className="p-4 space-y-2">`) immediately begin directly beneath the CampusOps brand header.
- Verified across all four roles:
  - **System Admin:** Removed.
  - **Technician:** Removed.
  - **Faculty:** Removed.
  - **Student:** Removed.
- Branding, navigation links, role-based link filtering, active item styling, mobile drawer (`mobileOpen`), and logout functionality were strictly preserved.

---

## 4. Removal of "Launch Scenario Simulator" Button Across All 4 Roles

### File Modified
`frontend/src/portals/admin/AdminDashboard.tsx`

### Implementation
- Removed the `Launch Scenario Simulator` button from the Operations Control Centre header.
- Removed both the `user?.sub_role === 'system_admin'` button and the default fallback branch.
- Removed the unused `Play` icon from the `lucide-react` import.
- Preserved role-specific administrative quick actions for `department_manager` (Approvals Queue), `facilities_admin` (Campus Readiness Center), and `procurement_approver` (Inventory & Parts).
- When a system administrator or default admin views the dashboard, the header layout aligns cleanly with no empty gap or awkward spacing.
- Other dashboards (`TechnicianDashboard.tsx`, `FacultyDashboard.tsx`, `StudentDashboard.tsx`) do not contain and never contained the simulator button.
- **Underlying Module Preservation:** The Scenario Simulator page (`ScenarioSimulatorView.tsx`), API endpoints, simulations test suite, and the sidebar menu item (`/admin/simulator`) were preserved intact.

---

## 5. Summary of Files Modified / Created

| File | Change Type | Purpose |
|---|---|---|
| `render.yaml` | Created | Render Static Site Blueprint with `/* -> /index.html` rewrite rule |
| `frontend/public/_redirects` | Created | Static hosting SPA redirect rule |
| `frontend/static.json` | Created | Static buildpack SPA configuration |
| `frontend/src/shared/components/NotFoundPage.tsx` | Created | Dedicated 404 Not Found error view |
| `frontend/src/app/router.tsx` | Modified | Added 404 route handling and `/admin/simulator` route alias |
| `frontend/src/shared/components/Sidebar.tsx` | Modified | Removed Active Portal section across all 4 roles |
| `frontend/src/portals/admin/AdminDashboard.tsx` | Modified | Removed Launch Scenario Simulator button and unused `Play` icon |

---

## 6. Verification & Build Results

### Frontend Build
Executed `npm --prefix frontend run build`:
```
> frontend@0.0.0 build
> tsc -b && vite build

vite v8.3.5 building client environment for production...
transforming...
✓ 2651 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.45 kB │ gzip:   0.29 kB
dist/assets/index-Dl0nFPT9.css   51.51 kB │ gzip:   9.64 kB
dist/assets/index-DB6nTFTz.js   963.06 kB │ gzip: 263.57 kB
✓ built in 313ms
```
- **TypeScript Errors:** 0
- **Build Exit Code:** 0
- **Asset Integrity:** `frontend/dist/_redirects` verified present in output bundle.

### Backend Test Suite
Executed relevant backend test suites (`test_role_separation.py`, `test_simulations.py`):
```
14 passed, 1 warning in 2.24s (Exit Code 0)
```
- Role separation, portal data guards, and simulation lifecycles remain completely intact.
- SQLite database `backend/data/campusops.db` remains untouched.

---

## 7. Render Deployment Instructions (Redeployment Required)

**Is a Render redeployment required?**  
**YES.** Static site code and rewrite rules must be deployed to Render for the changes to take effect in production.

### How to Apply the SPA Rewrite in Render:

#### Method 1: Automatic via Git (Recommended once pushed)
Once these changes are pushed to `main`, Render will automatically build and publish the new bundle. If the Render service was created from a Blueprint or syncs with `render.yaml`, the rewrite rule will be applied automatically.

#### Method 2: Manual Dashboard Configuration (Immediate & 100% Guaranteed)
If `overclock-26` was created as an individual "Static Site" directly in the Render dashboard:
1. Open the [Render Dashboard](https://dashboard.render.com).
2. Select the **overclock-26** Static Site.
3. In the left sidebar, click **Redirects/Rewrites**.
4. Click **Add Rule** and configure:
   - **Type:** `Rewrite`
   - **Source:** `/*`
   - **Destination:** `/index.html`
5. Click **Save Changes**.
6. Trigger a **Manual Deploy** -> **Deploy latest commit** (or push new commit).

---

## 8. Strictly Observed Restrictions
- **No commit or push performed** (per strict prompt instructions).
- **No automated deployment performed**.
- **No production data altered**.
- **Tracked SQLite database `backend/data/campusops.db` untouched**.
- **Scenario Simulator backend, views, and sidebar links preserved**.
- **RBAC and authentication mechanisms preserved intact**.

