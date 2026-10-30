import logging
import httpx
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger("whatsapp_ai_client")

class WhatsAppAIClient:
    """
    Communicates with the local Qwen GGUF / llama.cpp microservice via ngrok HTTPS or local address.
    Resilient to tunnel disconnects, network timeouts, and model errors.
    """

    def __init__(self):
        self.base_url = settings.AI_SERVICE_URL.rstrip("/")
        self.token = settings.AI_SERVICE_TOKEN
        self.timeout = float(settings.AI_TIMEOUT_SECONDS)

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            headers["X-AI-Token"] = self.token
        return headers

    async def check_health(self) -> Dict[str, Any]:
        """Probes the AI service health status."""
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(f"{self.base_url}/health", headers=self._get_headers())
                if res.status_code == 200:
                    return res.json()
                return {"status": "unhealthy", "code": res.status_code}
        except Exception as e:
            logger.warning(f"AI service health probe failed ({self.base_url}): {e}")
            return {"status": "offline", "error": str(e), "endpoint": self.base_url}

    async def classify_message(
        self,
        message: str,
        sender_role: str = "student",
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Sends message to Qwen for intent classification and entity extraction.
        Falls back to deterministic extraction if AI service is offline.
        """
        payload = {
            "message": message,
            "sender_role": sender_role,
            "conversation_history": conversation_history or []
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    f"{self.base_url}/ai/v1/classify",
                    json=payload,
                    headers=self._get_headers()
                )
                if res.status_code == 200:
                    return res.json()
                logger.error(f"AI classification error HTTP {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"AI service unreachable at {self.base_url}, engaging local rule fallback: {e}")

        # Local deterministic fallback so message is never lost
        return self._local_fallback_classify(message)

    async def generate_answer(
        self,
        query: str,
        context: Optional[str] = None,
        source_urls: Optional[List[str]] = None,
        sender_role: str = "student"
    ) -> Dict[str, Any]:
        """
        Synthesizes a grounded answer using Qwen.
        """
        payload = {
            "query": query,
            "context": context,
            "source_urls": source_urls or [],
            "sender_role": sender_role
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    f"{self.base_url}/ai/v1/answer",
                    json=payload,
                    headers=self._get_headers()
                )
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.warning(f"AI Q&A service unreachable at {self.base_url}: {e}")

        # Return fallback answer
        return {
            "answer": (
                "Sorry, I couldn't find reliable information about your query.\n\n"
                "Please try rephrasing your question or contact the concerned department for assistance."
            ),
            "grounded": False,
            "source_refs": source_urls or [],
            "confidence": 0.0,
            "fallback_required": True
        }

    def _local_fallback_classify(self, message: str) -> Dict[str, Any]:
        """Deterministic rule-based classification fallback."""
        import re
        lower = message.lower().strip()

        if lower in ["hi", "hello", "hey", "help"]:
            return {"intent": "GREETING", "confidence": 0.95, "description": "Greeting"}

        if any(t in lower for t in ["my tickets", "show tickets", "list tickets"]):
            return {"intent": "MY_TICKETS", "confidence": 0.92, "description": "List tickets"}

        if re.search(r"(?:cop|inc)-\d+", lower) or any(t in lower for t in ["status of", "check ticket"]):
            return {"intent": "TICKET_STATUS", "confidence": 0.90, "description": "Ticket status query"}

        issue_keys = ["broken", "not working", "leaking", "spark", "flicker", "failed", "outage", "fault", "dirty", "damaged", "no ac", "no wifi"]
        if any(k in lower for k in issue_keys):
            category = "Equipment"
            if any(k in lower for k in ["light", "power", "socket", "switch", "breaker", "spark", "blackout"]):
                category = "Electrical"
            elif any(k in lower for k in ["ac", "air condition", "cooling", "hvac"]):
                category = "HVAC"
            elif any(k in lower for k in ["projector", "screen", "mic", "podium"]):
                category = "Classroom"
            elif any(k in lower for k in ["wifi", "wi-fi", "internet", "network"]):
                category = "Network"

            room_match = re.search(r"(?:room|lab|hall)\s*([a-z0-9\-]+)", lower, re.IGNORECASE)
            room = room_match.group(1).upper() if room_match else None

            building = None
            for bld in ["Engineering", "Science", "Library", "Humanities", "Admin", "Innovation"]:
                if bld.lower() in lower:
                    building = f"{bld} Block"
                    break

            missing = []
            if not room and not building:
                missing.append("location")

            return {
                "intent": "REPORT_ISSUE",
                "category": category,
                "location": {"building": building, "room": room},
                "description": message,
                "priority_recommendation": "HIGH" if "urgent" in lower else "NORMAL",
                "confidence": 0.85,
                "missing_fields": missing,
                "requires_clarification": len(missing) > 0,
                "clarification_question": f"Which room or building is the {category.lower()} issue located in?" if missing else None
            }

        if any(k in lower for k in ["timing", "schedule", "when is", "library", "exam", "bus", "hostel", "policy"]):
            return {"intent": "CAMPUS_INFORMATION", "confidence": 0.88, "description": message}

        return {"intent": "GENERAL_QUESTION", "confidence": 0.75, "description": message}

whatsapp_ai_client = WhatsAppAIClient()

