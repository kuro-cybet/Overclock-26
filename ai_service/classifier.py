import re
import json
import logging
from typing import Dict, Any, List
from ai_service.llama_client import llama_client
from ai_service.schemas import ClassificationResponse, LocationEntity

logger = logging.getLogger("ai_service.classifier")

CLASSIFICATION_SYSTEM_PROMPT = """You are the CampusOps University Operations Intent & Entity Extraction Engine.
Analyze the user's message and output ONLY a valid JSON object without commentary or markdown codeblocks.

Available Intents:
- REPORT_ISSUE: User reports a physical fault, breakdown, maintenance requirement, hazard, or issue.
- TICKET_STATUS: User asks about the status or progress of a specific ticket or asks who is handling their issue.
- MY_TICKETS: User asks to view their active tickets or complaints.
- CAMPUS_INFORMATION: User asks about university schedules, library hours, timings, exam schedules, or procedures.
- GENERAL_QUESTION: User asks an informational/educational question (e.g., programming, academic theory, definition).
- GREETING: User says hello, hi, good morning, etc.
- FOLLOW_UP: User answers a clarification question or provides additional requested information.
- UNKNOWN: Meaning cannot be determined.

JSON Output Schema:
{
  "intent": "REPORT_ISSUE" | "TICKET_STATUS" | "MY_TICKETS" | "CAMPUS_INFORMATION" | "GENERAL_QUESTION" | "GREETING" | "FOLLOW_UP" | "UNKNOWN",
  "category": "Electrical" | "HVAC" | "Classroom" | "Network" | "Cleanliness" | "Safety" | "Plumbing" | "Equipment" | null,
  "subcategory": string | null,
  "location": {
    "building": string | null,
    "room": string | null
  },
  "description": string | null,
  "priority_recommendation": "LOW" | "NORMAL" | "HIGH" | "CRITICAL",
  "confidence": float between 0.0 and 1.0,
  "missing_fields": list of missing required fields (e.g., ["location"] if room/building is missing for REPORT_ISSUE),
  "requires_clarification": boolean,
  "clarification_question": string | null
}
"""

class IntentClassifier:
    async def classify(
        self,
        message: str,
        sender_role: str = "student",
        conversation_history: List[Dict[str, str]] = None
    ) -> ClassificationResponse:
        messages = [{"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT}]

        if conversation_history:
            for turn in conversation_history[-4:]:
                messages.append(turn)

        messages.append({
            "role": "user",
            "content": f"Sender Role: {sender_role}\nMessage: \"{message}\""
        })

        try:
            raw_output = await llama_client.chat_completion(
                messages=messages,
                temperature=0.1,
                max_tokens=600
            )
            parsed = self._extract_json(raw_output)
            if parsed:
                return ClassificationResponse(**parsed)
        except Exception as e:
            logger.warning(f"Llama inference failed or returned non-JSON, falling back to deterministic parser: {e}")

        # Deterministic regex fallback if local LLM is starting up or parsing fails
        return self._rule_based_fallback(message)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extracts JSON object from text, handling markdown fences and trailing text."""
        clean = text.strip()
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean, re.DOTALL)
        if match:
            clean = match.group(1)
        else:
            first_brace = clean.find("{")
            last_brace = clean.rfind("}")
            if first_brace != -1 and last_brace != -1:
                clean = clean[first_brace:last_brace + 1]

        data = json.loads(clean)
        # Normalize fields
        if "location" not in data or not isinstance(data["location"], dict):
            data["location"] = {"building": None, "room": None}
        return data

    def _rule_based_fallback(self, message: str) -> ClassificationResponse:
        """Deterministic safety fallback ensuring service never halts."""
        lower = message.lower().strip()

        # 1. Greetings
        if lower in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "help"]:
            return ClassificationResponse(
                intent="GREETING",
                confidence=0.98,
                description="User greeting"
            )

        # 2. Ticket Status & Inquiries
        if any(term in lower for term in ["my tickets", "show tickets", "list tickets", "all tickets"]):
            return ClassificationResponse(
                intent="MY_TICKETS",
                confidence=0.95,
                description="Requesting list of tickets"
            )

        ticket_code_match = re.search(r"(?:cop|inc)-\d{4,}-\d{2,4}|(?:cop|inc)-\d{3,5}", lower)
        if ticket_code_match or any(k in lower for k in ["status of", "check ticket", "progress of", "who is handling"]):
            return ClassificationResponse(
                intent="TICKET_STATUS",
                confidence=0.92,
                description=ticket_code_match.group(0).upper() if ticket_code_match else "Status query"
            )

        # 3. Issue reporting keywords
        issue_indicators = ["broken", "not working", "leaking", "spark", "flicker", "failed", "outage", "fault", "ac not", "no wifi", "dirty", "damaged", "projector"]
        is_issue = any(ind in lower for ind in issue_indicators)

        if is_issue:
            category = "Equipment"
            if any(k in lower for k in ["light", "power", "socket", "switch", "breaker", "spark", "shock", "blackout"]):
                category = "Electrical"
            elif any(k in lower for k in ["ac", "air condition", "cooling", "heater", "hvac", "temperature"]):
                category = "HVAC"
            elif any(k in lower for k in ["projector", "screen", "mic", "podium", "audio", "speaker", "board"]):
                category = "Classroom"
            elif any(k in lower for k in ["wifi", "wi-fi", "internet", "ethernet", "network", "router"]):
                category = "Network"
            elif any(k in lower for k in ["clean", "water", "toilet", "restroom", "trash", "dust"]):
                category = "Cleanliness"

            # Extract location details
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

            return ClassificationResponse(
                intent="REPORT_ISSUE",
                category=category,
                location=LocationEntity(building=building, room=room),
                description=message,
                priority_recommendation="HIGH" if any(u in lower for u in ["urgent", "exam", "immediately", "hazard"]) else "NORMAL",
                confidence=0.88,
                missing_fields=missing,
                requires_clarification=len(missing) > 0,
                clarification_question=f"Which room or building is the {category.lower()} issue located in?" if missing else None
            )

        # 4. Campus information query
        if any(k in lower for k in ["timing", "timings", "open", "schedule", "when is", "library", "exam", "bus", "hostel", "mess", "procedure", "policy"]):
            return ClassificationResponse(
                intent="CAMPUS_INFORMATION",
                confidence=0.90,
                description=message
            )

        # 5. General question
        return ClassificationResponse(
            intent="GENERAL_QUESTION",
            confidence=0.80,
            description=message
        )

classifier = IntentClassifier()

