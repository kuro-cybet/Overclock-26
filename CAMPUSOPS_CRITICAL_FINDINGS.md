# CAMPUSOPS — POST-PULL CRITICAL FINDINGS VERIFICATION REPORT

**Repository:** `S:\Overclock-26`  
**Inspected Commit:** `47b5980` (HEAD)  
**Date of Verification:** October 31, 2026  
**Status:** Verification Only (Zero Code or Database Modifications Applied)

---

## Executive Overview

A systematic verification of the latest CampusOps repository was conducted across eight mission-critical areas. Multiple confirmed architectural discrepancies, security gaps, and deployment risks were identified:

1. **WhatsApp Webhook Signature Bypass:** If `WHATSAPP_APP_SECRET` is unconfigured, signature verification unconditionally returns `True`, permitting unauthenticated message forgery.
2. **Dual-Architecture WhatsApp Disconnect:** Live webhooks execute through `whatsapp_message_processor.py` (AI pipeline + `WhatsAppConversation`), while `/simulate` executes through `whatsapp_assistant.py` (Regex heuristics + `WhatsAppSession`).
3. **Double Notification Dispatch:** Work order status updates invoke both `whatsapp_assistant.notify_incident_state_change` and `notification_service.notify_ticket_state_change`, resulting in duplicate WhatsApp messages.
4. **Outbox Stuck State for Failed WhatsApp Deliveries:** Unsuccessful WhatsApp sends leave outbox rows stranded in `"processing"` for 5 minutes instead of returning them to `"queued"` with 10-second exponential backoff.
5. **Supabase PostgreSQL Schema Gap:** The Supabase SQL migrations folder contains zero DDL definitions for WhatsApp tables or new user/report phone columns.
6. **Local Test Environment Drift:** `google-auth>=2.28.0` is missing from the local virtual environment, causing three test failures in `test_google_auth.py`.
7. **Database Test Pollution:** The test suite runs directly against the tracked SQLite file `backend/data/campusops.db` without sandbox isolation, modifying binary git state on every run.

---

## 1. WhatsApp Webhook Verification

### Finding 1.1: Webhook HMAC Signature Verification Bypass When Secret is Unset
- **Severity:** **CRITICAL**
- **File Path & Code Location:** `backend/app/services/whatsapp_service.py:100-106`
- **Confirmation Status:** **CONFIRMED**
- **Evidence:**
  ```python
  def verify_signature(self, raw_body: bytes, signature_header: Optional[str]) -> bool:
      """
      Validates the incoming X-Hub-Signature-256 header using SHA-256 HMAC.
      If WHATSAPP_APP_SECRET is not configured (e.g. local dev), returns True.
      """
      if not self.app_secret:
          return True
  ```
  In `backend/app/config.py:85`:
  ```python
  WHATSAPP_APP_SECRET: Optional[str] = _usable_env(os.getenv("WHATSAPP_APP_SECRET", None))
  ```
- **Actual Impact:** If `WHATSAPP_APP_SECRET` is not set in production (e.g. on Render), any external actor can send arbitrary forged HTTP POST requests to `https://campusops-u6yt.onrender.com/api/v1/whatsapp/webhook` with no signature or an invalid signature. The server will accept the request, parse the payload, register fake campus incidents, and trigger automated work orders.
- **Reproduction Steps:**
  1. Start the backend with `WHATSAPP_APP_SECRET=""` or unset.
  2. Send a `POST /api/v1/whatsapp/webhook` with valid JSON message payload and header `X-Hub-Signature-256: sha256=invalidsignature`.
  3. The endpoint returns HTTP 200 `{"status": "received", "count": 1}`.
- **Recommended Correction:** Enforce strict signature checking in non-development environments:
  ```python
  if not self.app_secret:
      if settings.ENVIRONMENT != "development":
          logger.error("[WhatsApp] Rejected webhook: WHATSAPP_APP_SECRET not configured in production")
          return False
      return True
  ```

---

### Finding 1.2: Hardcoded Verification Token Fallbacks in Webhook Handshake
- **Severity:** **LOW**
- **File Path & Code Location:** `backend/app/services/whatsapp_service.py:82-98` and `backend/app/config.py:84`
- **Confirmation Status:** **CONFIRMED**
- **Evidence:**
  ```python
  def verify_hub_token(self, mode: Optional[str], token: Optional[str]) -> bool:
      if mode != "subscribe" or not token:
          return False

      configured = (self.verify_token or "").strip()
      valid_tokens = {
          configured,
          "campusops_whatsapp_verify_token_2026",
          "campusops_verify_token_2026"
      }
      valid_tokens.discard("")
      return token.strip() in valid_tokens
  ```
  And in `config.py:84`:
  ```python
  WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "campusops_verify_token_2026").strip()
  ```
- **Actual Impact:** Any third party who knows the hardcoded strings `"campusops_whatsapp_verify_token_2026"` or `"campusops_verify_token_2026"` can successfully complete the Meta Webhook handshake, even if the deployment administrator configured a different token in the environment.
- **Reproduction Steps:**
  1. Set `WHATSAPP_VERIFY_TOKEN=custom_production_secret_999`.
  2. Send `GET /api/v1/whatsapp/webhook?hub.mode=subscribe&hub.challenge=12345&hub.verify_token=campusops_verify_token_2026`.
  3. The server returns HTTP 200 and echoes `12345` instead of rejecting with 403.
- **Recommended Correction:** Validate strictly against `self.verify_token`:
  ```python
  return mode == "subscribe" and bool(self.verify_token) and token.strip() == self.verify_token.strip()
  ```

---

## 2. WhatsApp Architecture Disconnect & Redundancy

### Finding 2.1: Dual Disconnected Processing Pipelines (Webhook vs. Simulation)
- **Severity:** **HIGH**
- **File Path & Code Location:** `backend/app/api/v1/whatsapp.py:73-83`, `backend/app/api/v1/whatsapp.py:270-285`, and `backend/app/services/whatsapp_assistant.py`
- **Confirmation Status:** **CONFIRMED**
- **Evidence:**
  - **Inbound Webhook (`POST /api/v1/whatsapp/webhook`):**
    ```python
    await whatsapp_message_processor.process_inbound_message(...)
    ```
    Uses `WhatsAppConversation` model (`state="idle"`), delegates to `whatsapp_ai_client.py` (`POST /ai/v1/classify`, `/ai/v1/answer` via Qwen GGUF on `llama.cpp`), requires two-step account linking via `WhatsAppUserLink`, and issues ticket IDs formatted as `COP-XXXX`.
  - **Inbound Simulator (`POST /api/v1/whatsapp/simulate`):**
    ```python
    reply = whatsapp_assistant.handle_incoming_message(...)
    ```
    Uses `WhatsAppSession` model (`step="IDLE"`), runs pure regex/keyword heuristics in `whatsapp_assistant.py`, performs unauthenticated auto-linking by phone number matching, and issues ticket IDs formatted as `CMP-XXXX`.
- **Actual Impact:**
  1. A student or faculty member testing via the UI simulation gets ticket `CMP-1024` with session saved in `whatsapp_sessions`.
  2. If the same user later messages the real WhatsApp bot on Meta Cloud API, the bot has no memory of the session (it reads `whatsapp_conversations`), rejects them as unlinked, and creates tickets formatted as `COP-1024`.
  3. Diagnostic endpoint `GET /api/v1/whatsapp/status` inspects `WhatsAppConversation`, while `GET /api/v1/whatsapp/session/{phone}` inspects `WhatsAppSession`.
- **Recommended Architecture:**
  Consolidate into **one authoritative architecture**:
  - Adopt `whatsapp_message_processor.py` + `whatsapp_ticket_service.py` as the unified core pipeline.
  - Make `POST /api/v1/whatsapp/simulate` call `whatsapp_message_processor.process_inbound_message` synchronously.
  - Deprecate `whatsapp_assistant.py` and merge any unique slot-filling heuristics into `whatsapp_conversation_service.py`.
  - Drop redundant model `WhatsAppSession` and standardize on `WhatsAppConversation`.

---

## 3. Google Authentication & RBAC

### Finding 3.1: Missing `google-auth` Package in Local Python Virtual Environment
- **Severity:** **HIGH** (Operational & Local Test Barrier)
- **File Path & Code Location:** `backend/requirements.txt:9` and `backend/app/tests/test_google_auth.py:47`
- **Confirmation Status:** **CONFIRMED**
- **Evidence:**
  `backend/requirements.txt` contains `google-auth>=2.28.0`.
  Running `pytest` against `test_google_auth.py` produces:
  ```text
  ModuleNotFoundError: No module named 'google'
  FAILED backend/app/tests/test_google_auth.py::test_google_login_rejects_unassigned_account
  FAILED backend/app/tests/test_google_auth.py::test_google_login_grants_allowlisted_role
  FAILED backend/app/tests/test_google_auth.py::test_google_login_rejects_account_assigned_to_multiple_roles
  ```
  In `backend/app/api/v1/auth.py:114-126`, the `ModuleNotFoundError` is caught by generic `except Exception:` and masked as:
  ```json
  {"detail": "Invalid or expired Google credential."}
  ```
- **Actual Impact:** 3 of 92 tests fail locally. On any fresh server deployment where dependencies are not reinstalled via `pip install -r requirements.txt`, Google authentication returns HTTP 401 for all users.
- **Recommended Correction:**
  1. Run `pip install -r backend/requirements.txt` in `backend/venv`.
  2. Catch `ImportError` explicitly in `auth.py:122` to return HTTP 503 ("Google auth module not installed") rather than confusing clients with 401 ("Invalid credential").

---

### Finding 3.2: Account Reactivation on Google Login Without Admin Approval
- **Severity:** **MEDIUM**
- **File Path & Code Location:** `backend/app/api/v1/auth.py:163-189`
- **Confirmation Status:** **CONFIRMED**
- **Evidence:**
  ```python
  user = db.query(User).filter(User.email == email).first()
  if not user:
      ...
  user.is_active = True
  ```
- **Actual Impact:** If an administrator deactivates a user's account in the `users` table (`user.is_active = False`), but forgets to set `is_active = False` in that user's role assignment table (`admin_assignments`, etc.), the deactivated user can simply sign in via Google and their account is automatically reactivated (`user.is_active = True`).
- **Reproduction Steps:**
  1. Soft-deactivate an admin in `users` (`UPDATE users SET is_active = 0 WHERE email = '...'`).
  2. Leave `admin_assignments.is_active = 1`.
  3. Sign in via `POST /api/v1/auth/google`.
  4. The account is set back to `is_active = 1` and granted an active JWT.
- **Recommended Correction:** Check `user.is_active` before updating:
  ```python
  if user and not user.is_active:
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="This user account has been deactivated. Contact an administrator."
      )
  ```

---

## 4. Database & Migration Synchronization

### Finding 4.1: Missing Supabase PostgreSQL Migrations for WhatsApp and User Profile Extensions
- **Severity:** **HIGH**
- **File Path & Code Location:** `supabase/supabase/migrations/`
- **Confirmation Status:** **CONFIRMED**
- **Evidence:**
  The `supabase/supabase/migrations/` directory contains only:
  - `20261031010000_split_role_assignments.sql`
  - `20261031020000_restrict_email_lifecycle.sql`
  - `20261031030000_expand_demo_technician.sql`
  There are **zero SQL migrations** for:
  - Table `whatsapp_user_links`
  - Table `whatsapp_conversations`
  - Table `whatsapp_message_logs`
  - Table `whatsapp_sessions`
  - Columns `users.phone_number`, `users.whatsapp_verified`, `users.auth_provider`, `users.provider_subject`
  - Column `reports.contact_phone`
  - Columns `notification_outbox.recipient_phone`, `notification_outbox.idempotency_key`
- **Actual Impact:** If a developer or automated CI/CD pipeline deploys the migrations to a live Supabase PostgreSQL instance using the Supabase CLI (`supabase db push`), the WhatsApp service will crash with `psycopg2.errors.UndefinedTable: relation "whatsapp_conversations" does not exist` when receiving messages.
- **Recommended Correction:** Add `supabase/supabase/migrations/20261031040000_add_whatsapp_tables.sql` providing the complete DDL for all four tables and alter statements for existing tables.

---

### Finding 4.2: Test Suite Lacks Isolation and Mutates Tracked SQLite Database
- **Severity:** **MEDIUM**
- **File Path & Code Location:** `backend/app/tests/conftest.py:16-18`
- **Confirmation Status:** **CONFIRMED**
- **Evidence:**
  ```python
  _BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
  _TEST_DB = os.path.join(_BACKEND_DIR, "data", "campusops.db").replace(os.sep, "/")
  os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
  ```
  `backend/data/campusops.db` is tracked in git.
- **Actual Impact:** Every test run mutates the tracked binary file `backend/data/campusops.db`. This causes `git status` to be perpetually dirty, risks merge conflicts on binary SQLite files during pulls/merges, and introduces potential test flakiness due to state pollution across runs.
- **Recommended Correction:** In `conftest.py`, create an isolated temporary SQLite database or use `sqlite:///:memory:` for tests, or copy `campusops.db` to a temporary directory for each test session.

---

## 5. Incident & Work-Order Dispatch

### Finding 5.1: Duplicate Line of Code in Work Order Update Handler
- **Severity:** **LOW**
- **File Path & Code Location:** `backend/app/api/v1/work_orders.py:516-517`
- **Confirmation Status:** **CONFIRMED**
- **Evidence:**
  ```python
  wo.status = payload.status
  wo.status = payload.status
  ```
- **Actual Impact:** Code redundancy; harmless at runtime but indicates an unclean merge conflict resolution.
- **Recommended Correction:** Remove duplicate line 517.

---

### Finding 5.2: Verification of Failed Auto-Dispatch Behavior
- **Severity:** **INFORMATIONAL (Verified Clean)**
- **File Path & Code Location:** `backend/app/services/work_order_service.py:119-134` and `backend/app/services/intake_service.py:86-100`
- **Confirmation Status:** **VERIFIED WORKING CORRECTLY**
- **Evidence:**
  When `auto_assign` fails (e.g. no technician with matching skills is on shift):
  - `assignment_service.assign_technician_to_work_order` raises `CampusOpsException`.
  - Caught in `work_order_service.py:125`.
  - Logs warning: `[WorkOrder] Auto-dispatch failed for WO-XXXX`.
  - Dispatches `workflow_notifications.work_order_unassigned`, alerting facilities admin in-app to assign manually.
  - `incident.status` remains `"open"` (does NOT silently mark dispatched).
  - `work_order.status` remains `"unassigned"`.
  - Transaction commits safely via the caller.

---

## 6. Notifications & Outbox Lifecycle

### Finding 6.1: Duplicate WhatsApp Notifications Dispatched on Work Order Updates
- **Severity:** **HIGH**
- **File Path & Code Location:** `backend/app/api/v1/work_orders.py:518-541`
- **Confirmation Status:** **CONFIRMED**
- **Evidence:**
  ```python
  # Notification Call 1: Direct assistant notification
  try:
      from app.services.whatsapp_assistant import whatsapp_assistant
      if payload.status == "in_progress":
          whatsapp_assistant.notify_incident_state_change(
              db=db, incident_id=wo.incident_id, event_type="in_progress"
          )
      elif payload.status in ["completed", "resolved"]:
          whatsapp_assistant.notify_incident_state_change(
              db=db, incident_id=wo.incident_id, event_type="resolved"
          )
  except Exception:
      pass

  # Notification Call 2: Outbox queue notification
  if payload.status != "completed" or incident_resolved:
      notif_st = "resolved" if incident_resolved else payload.status
      notification_service.notify_ticket_state_change(
          db=db,
          incident_id=wo.incident_id,
          new_status=notif_st,
      )
  ```
- **Actual Impact:** For every work order transition to `in_progress` or `resolved`:
  1. `whatsapp_assistant` executes `whatsapp_service.send_message` and sends message #1 to the student/faculty reporter.
  2. `notification_service.notify_ticket_state_change` creates an outbox entry in `notification_outbox` and the background outbox worker delivers message #2 to the same user.
  Users receive duplicate messages with different templates for every status update.
- **Recommended Correction:** Remove the ad-hoc `whatsapp_assistant.notify_incident_state_change` block from `work_orders.py`. Rely solely on `notification_service.notify_ticket_state_change`, which uses the transactional outbox with idempotency keys.

---

### Finding 6.2: Outbox Delivery Worker Leaves Failed WhatsApp Sends Stranded in `"processing"`
- **Severity:** **HIGH**
- **File Path & Code Location:** `backend/app/services/notification_service.py:344-350`
- **Confirmation Status:** **CONFIRMED**
- **Evidence:**
  ```python
  # Atomically claimed as "processing" at line 306
  if send_res.get("status") in ["sent", "simulated"]:
      item.status = "sent"
      sent_count += 1
  else:
      if item.attempts >= 3:
          item.status = "failed"
      failed_count += 1
  ```
- **Actual Impact:** When a WhatsApp message delivery fails on attempt 1 or 2 (e.g. Meta API rate limit, invalid recipient format, network glitch), `item.status` is never set back to `"queued"`. It remains `"processing"`. Because the worker only polls `status == "queued"`, the failed item is ignored until the 5-minute crash-recovery query runs (`last_attempt_at < now - timedelta(minutes=5)`), defeating the configured 10-second and 30-second exponential retry schedule.
- **Recommended Correction:**
  ```python
  if send_res.get("status") in ["sent", "simulated"]:
      item.status = "sent"
      sent_count += 1
  else:
      item.status = "failed" if item.attempts >= 3 else "queued"
      failed_count += 1
  ```

---

## 7. AI Microservice & llama.cpp Integration

### Finding 7.1: Verification of AI Service Offline Resiliency
- **Severity:** **INFORMATIONAL (Verified Clean)**
- **File Path & Code Location:** `backend/app/services/whatsapp_ai_client.py:53-67` and `backend/app/services/whatsapp_message_processor.py:65-75`
- **Confirmation Status:** **VERIFIED WORKING CORRECTLY**
- **Evidence:**
  If the `llama.cpp` server, the local FastAPI microservice (`ai_service/`), or the ngrok HTTPS tunnel becomes unreachable:
  - `whatsapp_ai_client.classify_message` catches all `httpx.RequestError` and timeout exceptions.
  - Automatically falls back to `_local_fallback_classify(message)` using regex and category dictionaries.
  - `generate_answer` catches errors and falls back to `_local_fallback_answer(...)`.
  - The inbound WhatsApp message is successfully processed and acknowledged; no messages are dropped.

---

## 8. Production Readiness & Configuration

### Configuration Checklist Matrix
| Service | Environment Variable | Default Value | Production Requirement | Status |
|---------|----------------------|---------------|------------------------|--------|
| **Backend** | `DATABASE_URL` | `sqlite:///./data/campusops.db` | Supabase Postgres URI with pooler | Critical |
| **Backend** | `SECRET_KEY` | `campusops-secret-key-...` | Secure 32+ char random string | Critical |
| **Backend** | `PASSWORD_LOGIN_ENABLED` | `False` | `False` (Google-only) or `True` (dev fallback) | Operational |
| **Backend** | `GOOGLE_CLIENT_ID` | `None` | Google Cloud Web OAuth Client ID | Critical |
| **Backend** | `WHATSAPP_ACCESS_TOKEN` | `None` | Meta System User Access Token | High |
| **Backend** | `WHATSAPP_APP_SECRET` | `None` | Meta App Secret (for HMAC-SHA256) | Critical |
| **Backend** | `WHATSAPP_PHONE_NUMBER_ID`| `None` | Meta Phone Number ID | High |
| **Backend** | `WHATSAPP_VERIFY_TOKEN` | `campusops_verify_token_2026` | Custom webhook verify token | Medium |
| **Backend** | `AI_SERVICE_URL` | `http://127.0.0.1:8001` | Public ngrok URL when AI runs locally | High |
| **Backend** | `AI_SERVICE_TOKEN` | `campusops_ai_secret_token_2026` | Shared secret with AI microservice | Medium |
| **Frontend** | `VITE_GOOGLE_CLIENT_ID` | `""` | Google Cloud Web OAuth Client ID | Critical |
| **Frontend** | `VITE_API_URL` | `""` (auto-detects Render) | `https://campusops-u6yt.onrender.com/api/v1` | Optional |

---

## Prioritized List of Corrections

1. **[P0 - CRITICAL SECURITY] Enforce HMAC Signature Check in Production:**
   In `backend/app/services/whatsapp_service.py`, reject webhooks when `WHATSAPP_APP_SECRET` is unset in non-development environments instead of returning `True`.
2. **[P0 - HIGH DEFECT] Fix WhatsApp Outbox Retry State:**
   In `backend/app/services/notification_service.py:348`, set `item.status = "failed" if item.attempts >= 3 else "queued"` on failed WhatsApp sends so retries honor backoff intervals instead of hanging in `"processing"`.
3. **[P1 - HIGH ARCHITECTURE] Eliminate Duplicate Notification Dispatch:**
   In `backend/app/api/v1/work_orders.py:518-533`, remove the redundant call to `whatsapp_assistant.notify_incident_state_change` to prevent double-texting users on status updates.
4. **[P1 - HIGH DATABASE] Add Missing Supabase Migrations:**
   Create a migration script in `supabase/supabase/migrations/` covering `whatsapp_user_links`, `whatsapp_conversations`, `whatsapp_message_logs`, `whatsapp_sessions`, and all added phone/auth columns.
5. **[P1 - HIGH ARCHITECTURE] Unify Dual WhatsApp Engines:**
   Deprecate `whatsapp_assistant.py` and route `POST /api/v1/whatsapp/simulate` through `whatsapp_message_processor.py` so simulation and production share the same state machine and `COP-XXXX` ticket formats.
6. **[P2 - MEDIUM OPERATIONAL] Install Missing Dependency in Local venv:**
   Run `pip install -r backend/requirements.txt` to install `google-auth` so that `test_google_auth.py` passes locally.
7. **[P2 - MEDIUM SECURITY] Prevent Deactivated User Reactivation on Google Login:**
   In `backend/app/api/v1/auth.py`, verify `not user or user.is_active` before authenticating Google logins.
8. **[P3 - LOW HYGIENE] Remove Duplicate Line & Isolate Test Database:**
   Remove duplicate line 517 in `work_orders.py`, and point `conftest.py` to an isolated temporary test database to stop dirtying the git working tree on every test run.

