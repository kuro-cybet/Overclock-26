import hashlib
import hmac
import json

import pytest

from app.config import settings
from app.integrations.gmail_sender import EmailDeliveryError, gmail_sender


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


def test_signature_matches_hmac(monkeypatch):
    monkeypatch.setattr(settings, "CAMPUSOPS_WEBHOOK_SECRET", "test-secret")

    expected = hmac.new(
        b"test-secret",
        b"1700000000.payload",
        hashlib.sha256,
    ).hexdigest()

    assert gmail_sender.sign("1700000000", "payload") == expected


def test_simulated_delivery_when_not_configured(monkeypatch):
    monkeypatch.setattr(gmail_sender, "_mode", "auto")
    monkeypatch.setattr(settings, "SUPABASE_URL", None)
    monkeypatch.setattr(settings, "CAMPUSOPS_WEBHOOK_SECRET", None)

    result = gmail_sender.send("student@campusops.edu", "Subject", "Body", "outbox-1")

    assert result.delivered is True
    assert result.simulated is True
    assert result.mode == "simulated"


def test_gmail_mode_requires_configuration(monkeypatch):
    monkeypatch.setattr(gmail_sender, "_mode", "gmail")
    monkeypatch.setattr(settings, "SUPABASE_URL", None)
    monkeypatch.setattr(settings, "CAMPUSOPS_WEBHOOK_SECRET", None)

    with pytest.raises(EmailDeliveryError):
        gmail_sender.send("student@campusops.edu", "Subject", "Body", "outbox-1")


def test_placeholder_supabase_url_stays_simulated(monkeypatch):
    monkeypatch.setattr(gmail_sender, "_mode", "auto")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://[YOUR-PROJECT-REF].supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_KEY", "[YOUR-SUPABASE-ANON-KEY]")
    monkeypatch.setattr(settings, "CAMPUSOPS_WEBHOOK_SECRET", "test-secret")

    result = gmail_sender.send("student@campusops.edu", "Subject", "Body", "outbox-1")

    assert result.mode == "simulated"


def test_gmail_delivery_posts_signed_payload(monkeypatch):
    monkeypatch.setattr(gmail_sender, "_mode", "gmail")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_KEY", "anon-key")
    monkeypatch.setattr(settings, "CAMPUSOPS_WEBHOOK_SECRET", "test-secret")
    monkeypatch.setattr(settings, "SUPABASE_EMAIL_FUNCTION", "send-campusops-email")

    captured = {}

    def fake_post(url, content=None, headers=None, timeout=None):
        captured.update(url=url, content=content, headers=headers, timeout=timeout)
        return FakeResponse(200, {"success": True, "gmail_message_id": "msg-123"})

    monkeypatch.setattr("app.integrations.gmail_sender.httpx.post", fake_post)

    result = gmail_sender.send(
        "student@campusops.edu",
        "Report received",
        "Your report was received.",
        "outbox-42",
    )

    assert result.delivered is True
    assert result.simulated is False
    assert result.mode == "gmail"
    assert result.message_id == "msg-123"

    assert captured["url"] == "https://project.supabase.co/functions/v1/send-campusops-email"
    assert captured["headers"]["apikey"] == "anon-key"
    assert captured["headers"]["Authorization"] == "Bearer anon-key"

    payload = json.loads(captured["content"])
    assert payload["event_type"] == "custom_email"
    assert payload["recipient_email"] == "student@campusops.edu"
    assert payload["entity_code"] == "outbox-42"
    assert payload["subject"] == "Report received"
    assert payload["body"] == "Your report was received."

    timestamp = captured["headers"]["x-campusops-timestamp"]
    signature = captured["headers"]["x-campusops-signature"]
    assert signature == gmail_sender.sign(timestamp, captured["content"])


def test_gmail_delivery_raises_on_function_error(monkeypatch):
    monkeypatch.setattr(gmail_sender, "_mode", "gmail")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_KEY", "anon-key")
    monkeypatch.setattr(settings, "CAMPUSOPS_WEBHOOK_SECRET", "test-secret")

    monkeypatch.setattr(
        "app.integrations.gmail_sender.httpx.post",
        lambda *args, **kwargs: FakeResponse(401, {"success": False, "error": "Invalid signature."}),
    )

    with pytest.raises(EmailDeliveryError):
        gmail_sender.send("student@campusops.edu", "Subject", "Body", "outbox-1")
