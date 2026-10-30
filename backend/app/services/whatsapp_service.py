import hmac
import hashlib
import logging
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
    """

    def __init__(self):
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.app_secret = settings.WHATSAPP_APP_SECRET
        self.verify_token = settings.WHATSAPP_VERIFY_TOKEN
        self.api_version = settings.WHATSAPP_API_VERSION or "v21.0"
        self.graph_url = f"https://graph.facebook.com/{self.api_version}"

    def verify_hub_token(self, mode: Optional[str], token: Optional[str]) -> bool:
        """Verifies Meta subscription handshake token."""
        return mode == "subscribe" and token == self.verify_token

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
                        # Handle button replies or list selections
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
        Sends an outbound text message through the Meta WhatsApp Cloud API.
        If credentials are not configured, records delivery safely in simulated mode.
        """
        clean_phone = recipient_phone.replace("+", "").replace("-", "").strip()

        if not self.access_token or not self.phone_number_id:
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

whatsapp_service = WhatsAppService()

