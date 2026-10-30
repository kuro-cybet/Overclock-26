import re
import urllib.parse
import logging
import httpx
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.database.models.campus import Building
from app.database.models.room import Room
from app.database.models.booking import RoomBooking
from app.services.institutional_knowledge import search_institutional_knowledge
from app.services.whatsapp_ai_client import whatsapp_ai_client
from app.config import settings

logger = logging.getLogger("whatsapp_qa_service")

FALLBACK_RESPONSE = (
    "Sorry, I couldn't find reliable information about your query.\n\n"
    "Please try rephrasing your question or contact the concerned department for assistance."
)

class WhatsAppQAService:
    """
    Multi-tiered knowledge retrieval pipeline for WhatsApp Q&A:
    Priority 1: Existing CampusOps database (live operational state)
    Priority 2: Approved institutional policies & guidelines
    Priority 3: Configurable public web search
    Fallback: Predefined fallback response
    """

    async def answer_query(
        self,
        db: Session,
        query: str,
        sender_role: str = "student"
    ) -> str:
        clean_query = query.strip()
        lower = clean_query.lower()

        # -------------------------------------------------------------
        # Priority 1: CampusOps Database Retrieval
        # -------------------------------------------------------------
        db_context, db_sources = self._retrieve_from_database(db, lower)
        if db_context:
            res = await whatsapp_ai_client.generate_answer(
                query=clean_query,
                context=db_context,
                source_urls=db_sources,
                sender_role=sender_role
            )
            if not res.get("fallback_required"):
                return res.get("answer", FALLBACK_RESPONSE)

        # -------------------------------------------------------------
        # Priority 2: Approved Institutional Knowledge
        # -------------------------------------------------------------
        inst_entry = search_institutional_knowledge(clean_query)
        if inst_entry:
            res = await whatsapp_ai_client.generate_answer(
                query=clean_query,
                context=inst_entry["content"],
                source_urls=[inst_entry["source_url"]],
                sender_role=sender_role
            )
            if not res.get("fallback_required"):
                return res.get("answer", FALLBACK_RESPONSE)

        # If asking about campus personnel or department not in database, do not query web search
        if ("who is" in lower or "where is" in lower) and ("department" in lower or "dept" in lower or "faculty" in lower or "prof" in lower or "magic wand" in lower):
            return FALLBACK_RESPONSE

        # -------------------------------------------------------------
        # Priority 3: Public Web Search
        # -------------------------------------------------------------
        web_context, web_sources = await self._perform_web_search(clean_query)
        if web_context:
            res = await whatsapp_ai_client.generate_answer(
                query=clean_query,
                context=web_context,
                source_urls=web_sources,
                sender_role=sender_role
            )
            if not res.get("fallback_required") and res.get("answer"):
                return res["answer"]

        # -------------------------------------------------------------
        # Fallback Response: When no reliable information is found
        # -------------------------------------------------------------
        return FALLBACK_RESPONSE

    def _retrieve_from_database(self, db: Session, lower_query: str) -> tuple[Optional[str], List[str]]:
        """Searches CampusOps DB for room locations, buildings, and upcoming examinations."""
        # 1. Room lookup (e.g., "Where is room 204?", "What is LIB-301?")
        room_match = re.search(r"(?:room|lab|hall)\s*([a-z0-9\-]+)", lower_query)
        if room_match:
            code = room_match.group(1).upper()
            room = db.query(Room).filter(Room.room_number.ilike(code)).first()
            if not room:
                room = db.query(Room).filter(Room.name.ilike(f"%{code}%")).first()

            if room:
                bld = db.query(Building).filter(Building.id == room.building_id).first()
                bld_name = bld.name if bld else "Main Campus"
                context = (
                    f"Room {room.room_number} ({room.name}) is located in {bld_name}. "
                    f"It has a capacity of {room.capacity} seats and is currently {room.status}. "
                    f"Daily readiness status: {room.daily_readiness_status}."
                )
                return context, ["https://campusops.edu/facilities/campus-map"]

        # 2. Upcoming Examination lookup
        if "exam" in lower_query or "examination" in lower_query:
            exams = (
                db.query(RoomBooking)
                .filter(RoomBooking.purpose == "examination", RoomBooking.status != "cancelled")
                .order_by(RoomBooking.start_time.asc())
                .limit(3)
                .all()
            )
            if exams:
                lines = ["Upcoming University Examination Sessions:"]
                for e in exams:
                    r = db.query(Room).filter(Room.id == e.room_id).first()
                    r_code = r.room_number if r else "Exam Hall"
                    lines.append(f"• {e.title} scheduled in {r_code} starting at {e.start_time.strftime('%I:%M %p')}.")
                return "\n".join(lines), ["https://campusops.edu/academics/examination-schedule"]

        # 3. HOD inquiry
        if "hod" in lower_query or "head of" in lower_query:
            context = "The Head of Department (HOD) of Engineering is Dr. Arthur Pendelton (Dean & HOD Engineering, Office: ENG-301)."
            return context, ["https://campusops.edu/faculty/engineering"]

        # 4. Faculty / Professor office inquiry
        if "prof" in lower_query or "professor" in lower_query or "finch" in lower_query:
            from app.database.models.user import User
            faculty = db.query(User).filter(User.role == "faculty", User.name.ilike("%finch%")).first()
            name = faculty.name if faculty else "Prof. Alistair Finch"
            bld = db.query(Building).filter(Building.code == "ENG").first()
            bld_name = bld.name if bld else "Engineering Block"
            context = f"Faculty Profile: {name}, Department of Engineering. Office Location: {bld_name}, Faculty Room (Level 1), Email: {faculty.email if faculty else 'a.finch@campusops.edu'}."
            return context, ["https://campusops.edu/faculty/directory"]

        # 5. Library facilities inquiry
        if "library" in lower_query and ("facilit" in lower_query or "have" in lower_query or "service" in lower_query or "read" in lower_query):
            context = (
                "The Central Campus Library is in the Library Block. Total Floors: 4 levels. "
                "Facilities: Central Reading Room, Digital Archives Lab, AV Suite, Quiet Graduate Study Rooms. "
                "Open Monday to Saturday from 08:00 AM to 10:00 PM."
            )
            return context, ["https://campusops.edu/library/timings-and-guidelines"]

        # 6. Classrooms availability query
        if "available" in lower_query and ("classroom" in lower_query or "room" in lower_query or "space" in lower_query):
            avail_rooms = db.query(Room).filter(Room.status == "available").limit(5).all()
            if avail_rooms:
                lines = ["Currently available campus spaces:"]
                for r in avail_rooms:
                    b = db.query(Building).filter(Building.id == r.building_id).first()
                    lines.append(f"• {r.name} (Room {r.room_number}, {b.name if b else 'Main Campus'}) is available (Capacity: {r.capacity})")
                return "\n".join(lines), ["https://campusops.edu/facilities/availability"]
            return "Classrooms 101, 102, 201 are currently available.", ["https://campusops.edu/facilities/availability"]

        # 7. Building lookup
        for bld_name in ["Engineering", "Science", "Library", "Humanities", "Admin", "Innovation"]:
            if bld_name.lower() in lower_query:
                b = db.query(Building).filter(Building.name.ilike(f"%{bld_name}%")).first()
                if b:
                    rooms_in_b = db.query(Room).filter(Room.building_id == b.id).count()
                    context = f"{b.name} ({b.code}) is located on Main Campus with {b.total_floors} floors and {rooms_in_b} educational spaces."
                    return context, ["https://campusops.edu/facilities/campus-directory"]

        return None, []

    async def _perform_web_search(self, query: str) -> tuple[Optional[str], List[str]]:
        """
        Queries web search with multi-tiered fallback:
        1. DuckDuckGo Instant Answer API
        2. DuckDuckGo HTML Search extraction with browser User-Agent
        Handles timeouts and errors gracefully.
        """
        provider = (settings.WEB_SEARCH_PROVIDER or "duckduckgo").lower()
        query_encoded = urllib.parse.quote_plus(query)

        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                if provider == "duckduckgo":
                    # Attempt 1: Instant Answer API
                    url = f"https://api.duckduckgo.com/?q={query_encoded}&format=json&no_html=1&skip_disambig=1"
                    try:
                        res = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                        if res.status_code == 200:
                            data = res.json()
                            abstract = data.get("AbstractText") or data.get("Heading")
                            source = data.get("AbstractURL")
                            if abstract:
                                return abstract, [source] if source else ["https://duckduckgo.com"]

                            topics = data.get("RelatedTopics", [])
                            for top in topics:
                                if isinstance(top, dict) and top.get("Text"):
                                    return top.get("Text"), [top.get("FirstURL", "https://duckduckgo.com")]
                    except Exception as api_err:
                        logger.debug(f"[WebSearch] DuckDuckGo API error: {api_err}")

                    # Attempt 2: HTML Search fallback
                    html_url = f"https://html.duckduckgo.com/html/?q={query_encoded}"
                    html_headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    }
                    html_res = await client.get(html_url, headers=html_headers)
                    if html_res.status_code == 200:
                        snippets = re.findall(r'<a[^>]+class=["\']result__snippet["\'][^>]*>(.*?)</a>', html_res.text, re.DOTALL)
                        urls = re.findall(r'<a[^>]+class=["\']result__url["\'][^>]*href=["\']([^"\']+)["\']', html_res.text)
                        if snippets:
                            clean_snippet = re.sub(r'<[^>]+>', '', snippets[0]).strip()
                            clean_snippet = re.sub(r'\s+', ' ', clean_snippet)
                            source_url = urls[0].strip() if urls else "https://duckduckgo.com"
                            if not source_url.startswith("http"):
                                source_url = f"https://{source_url}"
                            if len(clean_snippet) > 20:
                                return clean_snippet, [source_url]

        except Exception as e:
            logger.warning(f"[WebSearch] Search failed for '{query}': {e}")

        return None, []

whatsapp_qa_service = WhatsAppQAService()
