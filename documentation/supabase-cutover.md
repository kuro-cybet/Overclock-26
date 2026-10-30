# Supabase Cutover

CampusOps runs entirely on Supabase Postgres after this cutover. SQLite is only
used by the test suite, which runs against the tracked `backend/data/campusops.db`.

## 1. Get the database connection string

Supabase dashboard -> **Project Settings -> Database -> Connection string -> URI**.

Use the **pooler** host and replace `[YOUR-PASSWORD]` with the database password:

```
postgresql://postgres.pcmjjphqnjrebauyerdy:<PASSWORD>@aws-0-ap-south-1.pooler.supabase.com:5432/postgres
```

Port `5432` is session mode; port `6543` is transaction mode. Either works, but
session mode is safer for the migration script.

## 2. Migrate the data

From `backend/`, with `psycopg2-binary` installed (`pip install -r requirements.txt`):

```powershell
# First run: rebuild the schema cleanly, copy all 33 tables, lock down anon access.
python scripts/migrate_to_supabase.py --password "<DB_PASSWORD>" --recreate

# Re-runs without dropping anything (ON CONFLICT DO NOTHING):
python scripts/migrate_to_supabase.py --password "<DB_PASSWORD>"
```

The script copies every table the models define, verifies row counts, then:

* enables RLS on every `public` table, and
* revokes table/sequence access from `anon` and `authenticated`.

The API connects as the database owner (which bypasses RLS), so the app keeps
working while the public anon key can no longer read or write tables directly.
The Gmail Edge Function uses the service role and is unaffected.

Use `--no-lockdown` if you ever need the anon key to read a table directly.

## 3. Provision the demo accounts

If Supabase already has the legacy `public.role_assignments` table, first run
[`20261031010000_split_role_assignments.sql`](../supabase/supabase/migrations/20261031010000_split_role_assignments.sql)
in the Supabase SQL Editor. It creates the four role-specific tables and copies
the existing rows without dropping the old table, so the current backend keeps
working during deployment. Resolve any duplicate or unsupported roles reported
by the SQL before continuing.

Deploy the backend that reads the four tables, verify Google sign-in, and then
drop the old table in Supabase SQL Editor:

```sql
DROP TABLE public.role_assignments;
```

The provisioning command below can also migrate and remove the old table while
upserting the demo accounts.

Before deploying the email lifecycle changes, also run
[`20261031020000_restrict_email_lifecycle.sql`](../supabase/supabase/migrations/20261031020000_restrict_email_lifecycle.sql)
in SQL Editor. It tags existing queued emails as legacy so the updated backend
cancels them instead of sending them after deployment.

```powershell
python scripts/provision_roles.py --password "<DB_PASSWORD>"
```

This is idempotent. It:

* creates/updates the four demo accounts,
* records each one in its role-specific allowlist table,
* gives the technician a staff profile for auto-dispatch, and
* soft-deactivates the seeded `@campusops.edu` people (`is_active = false`).

Soft-deactivation keeps every report, incident, work order, booking,
notification and audit row attached to its original user. Use
`--keep-seeded-technicians` to leave the seeded technician pool active.

| Role | Email |
| --- | --- |
| `admin` / `system_admin` | `rajesekersudharsan@gmail.com` |
| `student` | `192573020.simats@saveetha.com` |
| `faculty` | `susen469@gmail.com` |
| `technician` / `maintenance_technician` | `techtroveversion3@gmail.com` |

Sign-in is Google-only: password login is disabled by default. The account
password can still be set with `--account-password`, and password login can be
re-enabled with `PASSWORD_LOGIN_ENABLED=true` if you need a local fallback.

## 4. Point the backend at Supabase

Set these on the Render backend service (`campusops-u6yt`), leaving the
existing Supabase/Gmail values untouched:

```
DATABASE_URL=postgresql://postgres.pcmjjphqnjrebauyerdy:<PASSWORD>@aws-0-ap-south-1.pooler.supabase.com:5432/postgres
GOOGLE_CLIENT_ID=<google-oauth-client-id>.apps.googleusercontent.com
```

Set this on the Render frontend service (`overclock-26`) and redeploy so the
Vite build picks it up:

```
VITE_GOOGLE_CLIENT_ID=<same client id>
```

Redeploy both. `backend/data/campusops.db` is no longer read once
`DATABASE_URL` starts with `postgres`.

## 5. Google sign-in

1. Google Cloud Console -> **APIs & Services -> Credentials**.
2. Create an **OAuth client ID** of type *Web application*.
3. Add authorized JavaScript origins:
   - `https://overclock-26.onrender.com`
   - `http://localhost:5173`
4. Put the client ID in `GOOGLE_CLIENT_ID` (backend) and
   `VITE_GOOGLE_CLIENT_ID` (frontend).

The frontend renders Google's official **Continue with Google** button and sends
the ID token to `POST /api/v1/auth/google`. The server verifies the token,
requires a verified email, and reads the role **only** from the matching role-specific
allowlist table (`admin_assignments`, `technician_assignments`,
`faculty_assignments`, or `student_assignments`).
An unassigned Google account gets `403`, and no role value is ever accepted from
the client.

## 6. Verify

```powershell
# Backend health
curl https://campusops-u6yt.onrender.com/health

# Password sign-in is disabled (expect 403)
curl -i https://campusops-u6yt.onrender.com/api/v1/auth/login -H "Content-Type: application/json" -d '{\"email\":\"rajesekersudharsan@gmail.com\",\"password\":\"password123\"}'

# The anon key must no longer read tables (expect an error / empty result)
curl "https://pcmjjphqnjrebauyerdy.supabase.co/rest/v1/users?select=email&limit=1" -H "apikey: <ANON_KEY>"
```

Open `https://overclock-26.onrender.com`, sign in with each of the four
accounts, and confirm:

* the reports, incidents, work orders and bookings from the local database are
  present (for example report `RPT-202610-0115`),
* **Continue with Google** appears, and each assigned Google account lands in
  its own portal,
* an unassigned Google account is refused.
