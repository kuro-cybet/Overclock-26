#!/usr/bin/env python3
"""
One-time Google OAuth helper for CampusOps Gmail delivery.

Runs a local loopback OAuth flow, then prints the refresh token and the exact
commands needed to store the credentials as Supabase Edge Function secrets.

Usage (PowerShell / cmd):
    python scripts\\google_oauth_setup.py

Or pass the client credentials directly:
    python scripts\\google_oauth_setup.py --client-id ... --client-secret ...

Google Cloud setup (one-time):
    1. https://console.cloud.google.com/  ->  create/select a project
    2. Enable "Gmail API"  (APIs & Services -> Library)
    3. OAuth consent screen -> External -> add your Google account as a Test user
    4. Credentials -> Create credentials -> OAuth client ID -> Desktop app
    5. Copy the client ID + client secret (Desktop clients accept any loopback port)

Requires no third-party packages.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
]


def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def build_auth_url(client_id: str, redirect_uri: str, scopes: list[str]) -> tuple[str, str, str]:
    state = secrets.token_urlsafe(24)
    verifier = secrets.token_urlsafe(64)
    challenge = b64url(hashlib.sha256(verifier.encode("ascii")).digest())

    query = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"{AUTH_URL}?{query}", state, verifier


def exchange_code(
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    verifier: str,
) -> dict:
    body = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "code_verifier": verifier,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        TOKEN_URL,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Token exchange failed (HTTP {exc.code}):\n{detail}")


def fetch_email(access_token: str) -> str | None:
    request = urllib.request.Request(
        USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8")).get("email")
    except (urllib.error.URLError, ValueError):
        return None


def wait_for_code(port: int, expected_state: str, timeout: int) -> str:
    result: dict[str, str] = {}

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib naming
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)

            if parsed.path != "/oauth2callback":
                self.send_response(404)
                self.end_headers()
                return

            if params.get("error"):
                result["error"] = params["error"][0]
            elif params.get("state", [""])[0] != expected_state:
                result["error"] = "state_mismatch"
            elif params.get("code"):
                result["code"] = params["code"][0]

            ok = "code" in result
            message = (
                "CampusOps: Google account connected. You can close this tab."
                if ok
                else f"CampusOps: authorization failed ({result.get('error', 'missing code')})."
            )
            page = (
                "<html><body style='font-family:system-ui;padding:3rem;text-align:center'>"
                f"<h2>{message}</h2></body></html>"
            ).encode("utf-8")

            self.send_response(200 if ok else 400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)

        def log_message(self, *_args) -> None:
            pass

    try:
        server = http.server.HTTPServer(("127.0.0.1", port), CallbackHandler)
    except OSError as exc:
        raise SystemExit(
            f"Could not listen on port {port}: {exc}\n"
            f"Pick another port with --port (and register it if you use a Web client)."
        )

    server.timeout = 1
    deadline = time.monotonic() + timeout

    with server:
        while not result and time.monotonic() < deadline:
            server.handle_request()

    if "code" not in result:
        raise SystemExit(
            f"Timed out after {timeout}s waiting for the browser callback. "
            f"Expected redirect URI: http://localhost:{port}/oauth2callback"
        )

    return result["code"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Google refresh token for CampusOps Gmail delivery.")
    parser.add_argument("--client-id", default=os.getenv("GOOGLE_CLIENT_ID"))
    parser.add_argument("--client-secret", default=os.getenv("GOOGLE_CLIENT_SECRET"))
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--timeout", type=int, default=300, help="Seconds to wait for the browser.")
    parser.add_argument("--no-browser", action="store_true", help="Print the URL instead of opening a browser.")
    parser.add_argument(
        "--scope",
        action="append",
        dest="scopes",
        help="Override scopes (repeatable). Defaults to gmail.send + userinfo.email.",
    )
    args = parser.parse_args()

    if not args.client_id or not args.client_secret:
        raise SystemExit(
            "Missing Google client credentials.\n"
            "Set GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET or pass "
            "--client-id and --client-secret."
        )

    redirect_uri = f"http://localhost:{args.port}/oauth2callback"
    scopes = args.scopes or DEFAULT_SCOPES

    auth_url, state, verifier = build_auth_url(args.client_id, redirect_uri, scopes)

    print("CampusOps - Google OAuth setup")
    print("=" * 60)
    print(f"Redirect URI : {redirect_uri}")
    print(f"Scopes       : {' '.join(scopes)}")
    print()
    print("If the browser does not open, paste this URL into it:")
    print(auth_url)
    print()

    if not args.no_browser:
        webbrowser.open(auth_url)

    code = wait_for_code(args.port, state, args.timeout)
    tokens = exchange_code(args.client_id, args.client_secret, code, redirect_uri, verifier)

    refresh_token = tokens.get("refresh_token")
    access_token = tokens.get("access_token")

    if not refresh_token:
        raise SystemExit(
            "Google did not return a refresh token.\n"
            "This usually means the account already granted access. Remove the app at "
            "https://myaccount.google.com/permissions and run this script again."
        )

    email = fetch_email(access_token) if access_token else None

    print()
    print("=" * 60)
    print("SUCCESS - store these as Supabase Edge Function secrets")
    print("=" * 60)
    print(f"GOOGLE_CLIENT_ID={args.client_id}")
    print(f"GOOGLE_CLIENT_SECRET={args.client_secret}")
    print(f"GOOGLE_REFRESH_TOKEN={refresh_token}")
    print(f"GOOGLE_SENDER_EMAIL={email or 'the Google account you just authorized'}")
    print()
    print("Supabase CLI:")
    print("  supabase secrets set \\")
    print(f"    GOOGLE_CLIENT_ID=\"{args.client_id}\" \\")
    print(f"    GOOGLE_CLIENT_SECRET=\"{args.client_secret}\" \\")
    print(f"    GOOGLE_REFRESH_TOKEN=\"{refresh_token}\" \\")
    print(f"    GOOGLE_SENDER_EMAIL=\"{email or 'YOUR_GMAIL_ADDRESS'}\" \\")
    print("    CAMPUSOPS_WEBHOOK_SECRET=\"YOUR_RANDOM_SECRET\" \\")
    print("    CAMPUSOPS_TEST_RECIPIENT=\"YOUR_INBOX@example.com\"")
    print()
    print("Or paste the values into: Supabase Dashboard -> Project Settings -> Edge Functions -> Secrets")
    print()
    print("Keep this refresh token secret. Re-running this script issues a new one.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
