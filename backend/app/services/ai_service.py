import re
from typing import Dict, Any, List, Optional
from difflib import SequenceMatcher

class AIServiceAdapter:
    """
    AI Extraction & Similarity Adapter.
    Processes unstructured issue reports into structured operational entities,
    detects duplicate reports using textual and spatial similarity, and generates summaries.
    """

    KEYWORD_CATEGORIES = {
        "network": ["wifi", "wi-fi", "internet", "ethernet", "router", "switch", "connection", "lan", "ping", "signal"],
        "classroom": ["projector", "screen", "podium", "mic", "microphone", "speaker", "sound", "smartboard", "hdmi"],
        "electrical": ["spark", "breaker", "power", "socket", "outlet", "light", "lights", "ups", "switchboard", "blackout"],
        "cleanliness": ["clean", "dirty", "trash", "spill", "sanitizer", "restroom", "toilet", "leak", "dust", "garbage"],
        "safety": ["fire", "alarm", "eyewash", "fume", "hazard", "blocked", "emergency", "exit", "door lock"],
        "equipment": ["computer", "pc", "workstation", "monitor", "oscilloscope", "printer", "3d printer", "instrument", "machine"]
    }

    BUILDING_KEYWORDS = {
        "Engineering Block": ["engineering", "eng", "robotics", "comp lab", "computer lab"],
        "Science Block": ["science", "sci", "chemistry", "physics", "biology", "chem lab"],
        "Library Block": ["library", "lib", "reading room", "archives"],
        "Humanities Block": ["humanities", "hum", "arts", "language lab"],
        "Administration Block": ["admin", "administration", "adm", "registrar", "security"],
        "Innovation Block": ["innovation", "inn", "maker space", "hpc", "startup", "incubator"]
    }

    ROOM_KEYWORDS = {
        "Computer Lab A": ["computer lab a", "comp lab a", "lab a", "101"],
        "Computer Lab B": ["computer lab b", "comp lab b", "lab b", "102"],
        "Robotics Workshop": ["robotics workshop", "robotics lab", "103"],
        "Engineering Lecture Hall 1": ["lecture hall 1", "eng lecture hall", "104"],
        "Engineering Examination Hall": ["exam hall", "examination hall", "301"]
    }

    def extract_incident_entities(self, text: str) -> Dict[str, Any]:
        lower = text.lower()

        # 1. Category extraction
        detected_category = "equipment"
        for cat, keywords in self.KEYWORD_CATEGORIES.items():
            if any(k in lower for k in keywords):
                detected_category = cat
                break

        # 2. Urgency & context detection
        urgency = "medium"
        context = "Standard operational report"
        if any(term in lower for term in ["exam", "examination", "test in", "minutes", "immediately", "urgent", "fire", "smoke", "spark"]):
            urgency = "critical"
            if "exam" in lower:
                context = "Upcoming examination"
            elif any(s in lower for s in ["fire", "smoke", "spark"]):
                context = "Hazardous safety condition"
        elif any(term in lower for term in ["class in", "lecture in", "starting soon", "important", "high"]):
            urgency = "high"
            context = "Active scheduled class"
        elif any(term in lower for term in ["when possible", "cosmetic", "minor", "low priority"]):
            urgency = "low"
            context = "Routine maintenance request"

        # 3. Location extraction
        detected_building = None
        for b_name, b_keys in self.BUILDING_KEYWORDS.items():
            if any(k in lower for k in b_keys):
                detected_building = b_name
                break

        # 4. Room extraction
        detected_room = None
        for r_name, r_keys in self.ROOM_KEYWORDS.items():
            if any(k in lower for k in r_keys):
                detected_room = r_name
                break

        # Default building if room found
        if detected_room and not detected_building:
            detected_building = "Engineering Block"

        # 5. Asset detection
        asset_detected = None
        if "wifi" in lower or "wi-fi" in lower:
            asset_detected = "Wi-Fi access point"
        elif "projector" in lower:
            asset_detected = "4K Laser Projector"
        elif "socket" in lower or "power" in lower:
            asset_detected = "Dual Power Socket"
        elif "ac" in lower or "air condition" in lower:
            asset_detected = "Central Inverter AC"
        elif "pc" in lower or "workstation" in lower:
            asset_detected = "Workstation Terminal"

        # 6. Missing details check
        missing_fields = []
        if not detected_building:
            missing_fields.append("building")
        if not detected_room:
            missing_fields.append("room")

        return {
            "category": detected_category,
            "category_label": "Network / Wi-Fi" if detected_category == "network" else detected_category.capitalize(),
            "location_building": detected_building,
            "location_room": detected_room,
            "urgency": urgency,
            "asset_candidate": asset_detected,
            "context": context,
            "confidence_score": 0.95 if (detected_building and detected_room) else 0.72,
            "missing_fields": missing_fields,
            "requires_clarification": len(missing_fields) > 0
        }

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        return SequenceMatcher(None, text_a.lower(), text_b.lower()).ratio()

    def find_duplicate_candidates(self, new_report_text: str, existing_reports: List[Dict[str, Any]], threshold: float = 0.55) -> List[Dict[str, Any]]:
        candidates = []
        for r in existing_reports:
            sim = self.compute_similarity(new_report_text, r.get("description", "") + " " + r.get("title", ""))
            # Boost score if they share the exact same room
            if r.get("room_id") and r.get("new_room_id") == r.get("room_id"):
                sim = min(1.0, sim + 0.25)
            if sim >= threshold:
                candidates.append({
                    "report_id": r.get("id"),
                    "report_code": r.get("report_code"),
                    "title": r.get("title"),
                    "similarity_score": round(sim, 2),
                    "existing_incident_id": r.get("incident_id")
                })
        candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
        return candidates

    def generate_incident_summary(self, reports: List[Dict[str, Any]]) -> str:
        count = len(reports)
        if count == 1:
            return f"Single incident record initiated from report {reports[0].get('report_code')}."
        return f"Correlated incident aggregating {count} user reports across the facility with shared symptoms and location proximity."

ai_service = AIServiceAdapter()

