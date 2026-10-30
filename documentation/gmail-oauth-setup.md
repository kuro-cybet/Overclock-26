# Gmail OAuth Setup

CampusOps sends transactional email through a Supabase Edge Function
(`send-campusops-email`), which calls the **Gmail API** using a Google OAuth 2.0
refresh token. The FastAPI backend never stores Google credentials — it only
signs an HMAC request and posts the queued email to the function.

```text
FastAPI outbox worker
  └─ HMAC-SHA256 signed POST ──► Supabase Edge Function (send-campusops-email)
                                    └─ refresh token ──► Google OAuth
                                            └────────────► Gmail API
```

When the credentials are missing, delivery is **simulated** so local development
and the test suite keep working. Set `EMAIL_DELIVERY_MODE=gmail` to make missing
credentials a hard failure instead.

---

## 1. Prepare Google Cloud (one time)

1. Open <https://console.cloud.google.com/> and create (or select) a project.
2. **APIs & Services → Library → Gmail API → Enable.**
3. **APIs & Services → OAuth consent screen**
   - User type: **External**
   - Add scopes: `https://www.googleapis.com/auth/gmail.send` and
     `https://www.googleapis.com/auth/userinfo.email`
   - Under **Test users**, add the Gmail account that will send the mail.
   - While the app is in *Testing*, refresh tokens expire after 7 days. Publish
     the app (or use an Internal app on Workspace) for long-lived tokens.
4. **APIs & Services → Credentials → Create credentials → OAuth client ID**
   - Application type: **Desktop app**
   - Desktop clients accept any `http://localhost:<port>` loopback redirect, so
     no redirect URI registration is needed.
5. Copy the **client ID** and **client secret**.

> The sender address is whatever Google account completed the consent screen.
> Gmail requires `From` to be that account (or a verified alias); the function
> sets `GOOGLE_SENDER_EMAIL` as the `From` address.

---

## 2. Generate the refresh token

From the repository root:

```powershell
$env:GOOGLE_CLIENT_ID="<client-id>.apps.googleusercontent.com"
$env:GOOGLE_CLIENT_SECRET="<client-secret>"
python scripts\google_oauth_setup.py
```

Or pass them as flags:

```powershell
python scripts\google_oauth_setup.py --client-id "..." --client-secret "..."
```

The script opens a browser, listens on `http://localhost:8765/oauth2callback`,
and prints:

```text
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REFRESH_TOKEN=...
GOOGLE_SENDER_EMAIL=...
```

Use `--port 9000` if 8765 is busy, and `--no-browser` on a headless machine
(copy the printed URL manually). If Google does not return a refresh token,
revoke the app at <https://myaccount.google.com/permissions> and re-run.

**Treat the refresh token like a password.** Re-running the script issues a new
one; the old token keeps working until revoked.

---

## 3. Store the Edge Function secrets

Choose one random value for `CAMPUSOPS_WEBHOOK_SECRET` and use the *same* value
in Supabase and in `backend/.env` (the two sides sign/verify with it).

```powershell
cd supabase
supabase secrets set `
  GOOGLE_CLIENT_ID="<client-id>.apps.googleusercontent.com" `
  GOOGLE_CLIENT_SECRET="<client-secret>" `
  GOOGLE_REFRESH_TOKEN="<refresh-token>" `
  GOOGLE_SENDER_EMAIL="campusops.notifications@gmail.com" `
  CAMPUSOPS_WEBHOOK_SECRET="<random-32+-char-secret>" `
  CAMPUSOPS_TEST_RECIPIENT="you@example.com" `
  CAMPUSOPS_ALWAYS_CC="you@example.com"
```

Or use **Supabase Dashboard → Project Settings → Edge Functions → Secrets**.
`CAMPUSOPS_TEST_RECIPIENT` caps the `test_email` event to a fixed inbox.

### Demo catch-all copy

Set `CAMPUSOPS_ALWAYS_CC` to receive a **Cc copy of every notification** while the
real recipient stays in `To:`:

```text
To: student@campusops.edu
Cc: suvedhansuveg14@gmail.com
```

If `CAMPUSOPS_ALWAYS_CC` is not set, the function falls back to
`CAMPUSOPS_TEST_RECIPIENT`. The copy is skipped when it would duplicate the
primary recipient. Unset both secrets to disable the catch-all.

---

## 4. Deploy the function

```powershell
cd supabase
supabase functions deploy send-campusops-email --no-verify-jwt
```

`verify_jwt = false` is intentional: callers are authenticated by the HMAC
signature plus timestamp, not a Supabase JWT.

---

## 5. Configure the backend

Copy `backend/.env.example` to `backend/.env` and fill in:

```dotenv
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_KEY=<anon-key>
CAMPUSOPS_WEBHOOK_SECRET=<same secret as above>
EMAIL_DELIVERY_MODE=auto        # auto | gmail | simulated
EMAIL_DELIVERY_TIMEOUT_SECONDS=15
```

Restart the backend. `GET /api/v1/notifications/outbox/status` and the
`delivery_mode` field returned by `POST /api/v1/notifications/outbox/process`
show whether real Gmail delivery is active. Both endpoints require a
`system_admin` bearer token.

---

## 6. Test it end to end

**a. Edge function only** (bypasses the backend):

```powershell
cd supabase\supabase
$env:CAMPUSOPS_WEBHOOK_SECRET="<secret>"
$env:SUPABASE_ANON_KEY="<anon-key>"
node test-email.mjs
```

Expected: `HTTP Status: 200` with `"success": true` and a `gmail_message_id`.

**b. Through the backend outbox:**

Both integration endpoints are protected now. Either log in as a system admin or
sign the raw body with `CAMPUSOPS_INBOUND_SECRET` (fallback:
`CAMPUSOPS_WEBHOOK_SECRET`) using the same `timestamp.body` HMAC scheme as the
edge function.

```powershell
# 0. Log in once; every call below uses this token
$login = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/auth/login `
  -ContentType "application/json" `
  -Body '{"email":"admin@campusops.edu","password":"password123"}'
$headers = @{ Authorization = "Bearer $($login.access_token)" }

# 1. Queue a notification
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/integrations/email/inbox `
  -Headers $headers -ContentType "application/json" `
  -Body '{"sender_email":"student@campusops.edu","subject":"Wi-Fi down in Lab A","body":"No connectivity since 9am."}'

# 2. Trigger processing
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/notifications/outbox/process `
  -Headers $headers
```

The response should report `"delivery_mode": "gmail"` and `"sent": 1`, the
acknowledgement email should arrive in the recipient inbox, and a copy should
land in `CAMPUSOPS_ALWAYS_CC` (or `CAMPUSOPS_TEST_RECIPIENT`). The background
outbox worker also processes queued mail every 5 seconds, so the manual trigger
may return `"sent": 0` if the worker already delivered it.

---

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| `Google OAuth token refresh failed.` | Refresh token revoked/expired, wrong client ID/secret, or Gmail account removed from Test users. Re-run the setup script. |
| `invalid_grant` | Token expired (Testing-mode apps expire in 7 days) or already rotated. Generate a new token. |
| `Gmail API request failed with HTTP 403` | Gmail API not enabled, or the authorized account lacks the `gmail.send` scope. |
| `Gmail API request failed with HTTP 400` | `GOOGLE_SENDER_EMAIL` does not match the authorized account. Use the same address. |
| `Invalid or expired request signature.` | `CAMPUSOPS_WEBHOOK_SECRET` differs between backend and Supabase, or the machine clock is >5 minutes off. |
| `Email delivery failed. Check function logs.` | Inspect `supabase functions logs send-campusops-email`; the backend sanitises errors on purpose. |
| Emails silently simulated | `SUPABASE_URL` or `CAMPUSOPS_WEBHOOK_SECRET` is empty in `backend/.env`. Check `delivery_mode`. |
| Real recipients get mail but the demo inbox doesn't | `CAMPUSOPS_ALWAYS_CC` and `CAMPUSOPS_TEST_RECIPIENT` are both empty, or the copy address equals the recipient. |
| Function deploy can't find config | Run the command from the `supabase/` directory (the CLI locates `supabase/supabase/config.toml`). |

## Files involved

| File | Role |
| --- | --- |
| `scripts/google_oauth_setup.py` | One-time loopback OAuth flow that prints the refresh token. |
| `supabase/supabase/functions/send-campusops-email/index.ts` | Verifies the HMAC signature and sends via Gmail API. |
| `backend/app/integrations/gmail_sender.py` | Signs and posts outbox messages to the edge function. |
| `backend/app/services/notification_service.py` | Outbox retry/backoff loop that calls the sender. |
| `backend/app/config.py` | `EMAIL_DELIVERY_MODE`, `CAMPUSOPS_WEBHOOK_SECRET`, function URL. |
