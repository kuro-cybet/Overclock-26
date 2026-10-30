import hmac
import hashlib
import logging
import uuid
from typing import Dict, Any, Optional, List
import httpx
from sqlalchemy.orm import Session
from app.config import settings
from app.database.models.whatsapp import WhatsAppMessageLog

logger = logging.getLogger("whatsapp_service")

class WhatsAppService:
    """
    Handles Meta WhatsApp Cloud API communications:
    - Webhook verification & HMAC signature validation
    - Inbound message parsing & deduplication
    - Outbound message delivery via Meta Graph API
    - Simulation mode fallback for development and testing
    """

    def __init__(self):
        self._access_token: Optional[str] = None
        self._phone_number_id: Optional[str] = None
        self._app_secret: Optional[str] = None
        self._verify_token: Optional[str] = None
        self._api_version: Optional[str] = None
        self._simulate: Optional[bool] = None

    @property
    def access_token(self) -> Optional[str]:
        return self._access_token if self._access_token is not None else settings.WHATSAPP_ACCESS_TOKEN

    @access_token.setter
    def access_token(self, value: Optional[str]):
        self._access_token = value

    @property
    def phone_number_id(self) -> Optional[str]:
        return self._phone_number_id if self._phone_number_id is not None else settings.WHATSAPP_PHONE_NUMBER_ID

    @phone_number_id.setter
    def phone_number_id(self, value: Optional[str]):
        self._phone_number_id = value

    @property
    def app_secret(self) -> Optional[str]:
        return self._app_secret if self._app_secret is not None else settings.WHATSAPP_APP_SECRET

    @app_secret.setter
    def app_secret(self, value: Optional[str]):
        self._app_secret = value

    @property
    def verify_token(self) -> str:
        return self._verify_token if self._verify_token is not None else settings.WHATSAPP_VERIFY_TOKEN

    @verify_token.setter
    def verify_token(self, value: str):
        self._verify_token = value

    @property
    def api_version(self) -> str:
        return self._api_version if self._api_version is not None else (settings.WHATSAPP_API_VERSION or "v21.0")

    @api_version.setter
    def api_version(self, value: str):
        self._api_version = value

    @property
    def simulate(self) -> bool:
        return self._simulate if self._simulate is not None else settings.WHATSAPP_SIMULATE

    @simulate.setter
    def simulate(self, value: bool):
        self._simulate = value

    @property
    def graph_url(self) -> str:
        return f"https://graph.facebook.com/{self.api_version}"

    def verify_hub_token(self, mode: Optional[str], token: Optional[str]) -> bool:
        """
        Verifies Meta subscription handshake token.
        Requires mode == 'subscribe' and token to match either the configured WHATSAPP_VERIFY_TOKEN
        or the standard campusops verify tokens.
        """
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

    def verify_signature(self, raw_body: bytes, signature_header: Optional[str]) -> bool:
        """
        Validates the incoming X-Hub-Signature-256 header using SHA-256 HMAC.
        If WHATSAPP_APP_SECRET is not configured (e.g. local dev), returns True.
        """
        if not self.app_secret:
            return True

        if not signature_header or not signature_header.startswith("sha256="):
            logger.warning("[WhatsApp] Missing or malformed X-Hub-Signature-256 header")
            return False

        expected_sig = signature_header.split("=")[1]
        mac = hmac.new(
            key=self.app_secret.encode("utf-8"),
            msg=raw_body,
            digestmod=hashlib.sha256
        )
        calculated_sig = mac.hexdigest()
        return hmac.compare_digest(calculated_sig, expected_sig)

    def is_message_duplicate(self, db: Session, message_id: str) -> bool:
        """Checks if Meta message ID has already been recorded in the audit log."""
        if not message_id:
            return False
        existing = db.query(WhatsAppMessageLog).filter(WhatsAppMessageLog.message_id == message_id).first()
        return existing is not None

    def log_message(
        self,
        db: Session,
        message_id: str,
        sender_phone: str,
        recipient_phone: str,
        direction: str,
        content: str,
        status: str = "received",
        error_details: Optional[str] = None
    ) -> WhatsAppMessageLog:
        """Persists message log into whatsapp_messages_log table."""
        log = WhatsAppMessageLog(
            message_id=message_id,
            sender_phone=sender_phone,
            recipient_phone=recipient_phone,
            direction=direction,
            content=content,
            status=status,
            error_details=error_details
        )
        db.add(log)
        db.commit()
        return log

    def parse_webhook_messages(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extracts incoming message events from Meta webhook payload.
        Returns a structured list of message dictionaries.
        """
        parsed_messages = []
        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                metadata = value.get("metadata", {})
                recipient_number = metadata.get("display_phone_number", "CampusOps")

                for msg in messages:
                    msg_id = msg.get("id")
                    from_number = msg.get("from")
                    msg_type = msg.get("type")
                    text_body = ""

                    if msg_type == "text":
                        text_body = msg.get("text", {}).get("body", "")
                    elif msg_type == "interactive":
                        interactive = msg.get("interactive", {})
                        if interactive.get("type") == "button_reply":
                            text_body = interactive.get("button_reply", {}).get("title", "")
                        elif interactive.get("type") == "list_reply":
                            text_body = interactive.get("list_reply", {}).get("title", "")

                    if msg_id and from_number and text_body:
                        parsed_messages.append({
                            "message_id": msg_id,
                            "sender_phone": from_number,
                            "recipient_phone": recipient_number,
                            "message_type": msg_type,
                            "text": text_body.strip(),
                            "timestamp": msg.get("timestamp")
                        })

        return parsed_messages

    async def send_text_message(self, recipient_phone: str, message_text: str) -> Dict[str, Any]:
        """
        Sends an outbound text message through the Meta WhatsApp Cloud API asynchronously.
        If credentials are not configured or WHATSAPP_SIMULATE is true, records delivery safely in simulated mode.
        """
        clean_phone = recipient_phone.replace("+", "").replace("-", "").replace(" ", "").strip()

        if self.simulate or not self.access_token or not self.phone_number_id:
            logger.info(f"[WhatsApp SIMULATED] To: {clean_phone} | Message: {message_text[:120]}...")
            return {
                "status": "simulated",
                "recipient": clean_phone,
                "message_preview": message_text[:100]
            }

        url = f"{self.graph_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message_text
            }
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code in [200, 201]:
                    data = res.json()
                    logger.info(f"[WhatsApp SENT] To: {clean_phone} | Result: {data}")
                    return {"status": "sent", "data": data}
                else:
                    err_text = res.text
                    logger.error(f"[WhatsApp API ERROR] HTTP {res.status_code}: {err_text}")
                    return {"status": "failed", "error": err_text, "code": res.status_code}
        except Exception as e:
            logger.error(f"[WhatsApp Exception] Failed to send message to {clean_phone}: {e}")
            return {"status": "failed", "error": str(e)}

    def send_message(
        self,
        recipient_phone: Optional[str] = None,
        message_text: Optional[str] = None,
        to_phone: Optional[str] = None,
        text: Optional[str] = None,
        db: Optional[Session] = None,
        notification_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synchronous outbound text message helper.
        Supports direct sending via Meta Cloud API or recording in simulated mode.
        Optionally persists an audit log entry and outbox entry when a db session is provided.
        """
        phone_target = recipient_phone or to_phone or ""
        msg_target = message_text or text or ""
        clean_phone = phone_target.replace("+", "").replace("-", "").replace(" ", "").strip()

        # If notification_type is provided, persist into NotificationOutbox for queue tracking
        if notification_type and db:
            from app.database.models.notification import NotificationOutbox
            outbox_entry = NotificationOutbox(
                recipient_email=f"{clean_phone}@whatsapp.campusops.edu",
                recipient_phone=f"+{clean_phone}",
                channel="whatsapp",
                subject=notification_type,
                body=msg_target,
                status="sent" if (not self.simulate and self.access_token) else "queued"
            )
            db.add(outbox_entry)
            db.commit()

        if self.simulate or not self.access_token or not self.phone_number_id:
            logger.info(f"[WhatsApp SIMULATED] To: {clean_phone} | Message: {msg_target[:120]}...")
            if db:
                msg_id = f"out_sim_{uuid.uuid4().hex[:12]}"
                self.log_message(
                    db=db,
                    message_id=msg_id,
                    sender_phone=self.phone_number_id or "CampusOps",
                    recipient_phone=clean_phone,
                    direction="outbound",
                    content=msg_target,
                    status="simulated"
                )
            return {
                "status": "simulated",
                "recipient": clean_phone,
                "message_preview": msg_target[:100]
            }

        url = f"{self.graph_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": msg_target
            }
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, json=payload, headers=headers)
                if res.status_code in [200, 201]:
                    data = res.json()
                    logger.info(f"[WhatsApp SENT] To: {clean_phone} | Result: {data}")
                    if db:
                        msg_id = data.get("messages", [{}])[0].get("id") or f"out_{uuid.uuid4().hex[:12]}"
                        self.log_message(
                            db=db,
                            message_id=msg_id,
                            sender_phone=self.phone_number_id or "CampusOps",
                            recipient_phone=clean_phone,
                            direction="outbound",
                            content=msg_target,
                            status="sent"
                        )
                    return {"status": "sent", "data": data}
                else:
                    err_text = res.text
                    logger.error(f"[WhatsApp API ERROR] HTTP {res.status_code}: {err_text}")
                    if db:
                        msg_id = f"out_err_{uuid.uuid4().hex[:12]}"
                        self.log_message(
                            db=db,
                            message_id=msg_id,
                            sender_phone=self.phone_number_id or "CampusOps",
                            recipient_phone=clean_phone,
                            direction="outbound",
                            content=msg_target,
                            status="failed",
                            error_details=err_text
                        )
                    return {"status": "failed", "error": err_text, "code": res.status_code}
        except Exception as e:
            logger.error(f"[WhatsApp Exception] Failed to send message to {clean_phone}: {e}")
            return {"status": "failed", "error": str(e)}

whatsapp_service = WhatsAppService()
