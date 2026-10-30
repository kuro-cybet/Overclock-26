"""
Gmail delivery through the `send-campusops-email` Supabase Edge Function.

The edge function owns the Google OAuth credentials and talks to the Gmail API.
This module only signs an HMAC-SHA256 request and posts the email payload to it,
so the backend never stores a Google refresh token.

Set the following environment variables to enable real delivery:
    SUPABASE_URL, SUPABASE_KEY (anon key), CAMPUSOPS_WEBHOOK_SECRET

When they are missing (or EMAIL_DELIVERY_MODE=simulated) delivery is simulated
and the outbox keeps working exactly as it did before.
"""

import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

DELIVERY_MODES = ("auto", "gmail", "simulated")
MAX_SUBJECT_LENGTH = 200
MAX_BODY_LENGTH = 20_000


class EmailDeliveryError(RuntimeError):
    """Raised when an email could not be handed off to the edge function."""


def _usable(value: Optional[str]) -> bool:
    return bool(value and value.strip() and "[" not in value and "]" not in value)


@dataclass(frozen=True)
class DeliveryResult:
    delivered: bool
    simulated: bool
    message_id: Optional[str] = None
    mode: str = "simulated"


class GmailSender:
    def __init__(self) -> None:
        self._mode = (settings.EMAIL_DELIVERY_MODE or "auto").lower()
        if self._mode not in DELIVERY_MODES:
            logger.warning(
                "[Gmail] Unknown EMAIL_DELIVERY_MODE=%r, falling back to 'auto'.",
                self._mode,
            )
            self._mode = "auto"

    @property
    def configured(self) -> bool:
        """True when every credential needed for real delivery is present."""
        return (
            _usable(settings.email_function_url)
            and _usable(settings.CAMPUSOPS_WEBHOOK_SECRET)
            and _usable(settings.SUPABASE_KEY)
        )

    @property
    def mode(self) -> str:
        if self._mode == "simulated":
            return "simulated"
        if self._mode == "gmail":
            return "gmail"
        return "gmail" if self.configured else "simulated"

    def sign(self, timestamp: str, raw_body: str) -> str:
        secret = settings.CAMPUSOPS_WEBHOOK_SECRET
        if not secret:
            raise EmailDeliveryError("CAMPUSOPS_WEBHOOK_SECRET is not configured.")
        return hmac.new(
            secret.encode("utf-8"),
            f"{timestamp}.{raw_body}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _build_payload(
        self,
        recipient: str,
        subject: str,
        body: str,
        entity_code: str,
        recipient_name: Optional[str] = None,
    ) -> dict:
        return {
            "event_type": "custom_email",
            "entity_code": entity_code,
            "recipient_email": recipient,
            "recipient_name": recipient_name or "",
            "subject": subject[:MAX_SUBJECT_LENGTH],
            "body": body[:MAX_BODY_LENGTH],
        }

    def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        entity_code: str,
        recipient_name: Optional[str] = None,
    ) -> DeliveryResult:
        if self.mode == "simulated":
            logger.info(
                "[Gmail] Simulated delivery to %s (set GOOGLE_* and SUPABASE_* secrets to send for real).",
                recipient,
            )
            return DeliveryResult(delivered=True, simulated=True, mode="simulated")

        if not self.configured:
            raise EmailDeliveryError(
                "Gmail delivery is enabled but SUPABASE_URL, SUPABASE_KEY or "
                "CAMPUSOPS_WEBHOOK_SECRET is missing."
            )

        payload = self._build_payload(recipient, subject, body, entity_code, recipient_name)
        raw_body = json.dumps(payload, separators=(",", ":"))
        timestamp = str(int(time.time()))
        signature = self.sign(timestamp, raw_body)

        headers = {
            "Content-Type": "application/json",
            "x-campusops-timestamp": timestamp,
            "x-campusops-signature": signature,
        }
        if settings.SUPABASE_KEY:
            # Supabase's function gateway expects the anon key for project-owned functions.
            headers["apikey"] = settings.SUPABASE_KEY
            headers["Authorization"] = f"Bearer {settings.SUPABASE_KEY}"

        try:
            response = httpx.post(
                settings.email_function_url,
                content=raw_body,
                headers=headers,
                timeout=settings.EMAIL_DELIVERY_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError as exc:
            raise EmailDeliveryError(f"Could not reach the email function: {exc}") from exc

        try:
            data = response.json()
        except ValueError:
            data = {}

        if response.status_code >= 400 or not data.get("success"):
            error = data.get("error") or f"HTTP {response.status_code}"
            raise EmailDeliveryError(f"Email function rejected the message: {error}")

        return DeliveryResult(
            delivered=True,
            simulated=False,
            message_id=data.get("gmail_message_id"),
            mode="gmail",
        )


gmail_sender = GmailSender()
