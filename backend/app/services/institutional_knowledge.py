from typing import List, Dict, Any, Optional

INSTITUTIONAL_KNOWLEDGE_ENTRIES: List[Dict[str, Any]] = [
    {
        "topic": "library_hours",
        "title": "University Central Library Timings & Policies",
        "keywords": ["library", "timings", "hours", "reading room", "open", "books", "borrow"],
        "content": (
            "The University Central Library is located in the Library Block.\n"
            "• Operating Hours: Monday through Saturday from 08:00 AM to 10:00 PM. Sunday: 10:00 AM to 06:00 PM.\n"
            "• Graduate Quiet Reading Room (LIB-301) is open 24/7 during official examination weeks.\n"
            "• Students may borrow up to 4 books simultaneously for 14 days with standard student ID."
        ),
        "source_url": "https://campusops.edu/library/timings-and-guidelines"
    },
    {
        "topic": "examination_procedures",
        "title": "University Examination Code of Conduct & Readiness",
        "keywords": ["exam", "examination", "test", "hall", "procedure", "rules", "admit card", "hall ticket"],
        "content": (
            "Official Examination Guidelines:\n"
            "• Students must report to assigned examination rooms 20 minutes prior to paper commencement.\n"
            "• Hall tickets and valid physical student ID cards are mandatory for entry.\n"
            "• Mobile phones, smartwatches, and unauthorized electronics are strictly prohibited in exam halls.\n"
            "• Faculty conduct physical daily readiness checks 45 minutes before each examination slot."
        ),
        "source_url": "https://campusops.edu/academics/examination-protocols"
    },
    {
        "topic": "maintenance_reporting",
        "title": "Procedure for Reporting Campus Maintenance & Equipment Faults",
        "keywords": ["maintenance", "report", "fault", "complaint", "procedure", "ticket", "sla", "repair"],
        "content": (
            "CampusOps Maintenance Reporting Procedure:\n"
            "• Students and faculty can report faults instantly via WhatsApp or the CampusOps Web Portal.\n"
            "• P1 Critical issues (power outage, water leaks, exam room faults) receive immediate technician dispatch with a 2-hour SLA resolution window.\n"
            "• P2/P3 standard operational repairs have response SLAs between 4 and 12 hours.\n"
            "• Technicians update progress in real-time, triggering automatic WhatsApp status notifications to the reporter."
        ),
        "source_url": "https://campusops.edu/operations/maintenance-handbook"
    },
    {
        "topic": "transport_shuttle",
        "title": "Campus Transportation & Shuttle Bus Schedule",
        "keywords": ["bus", "transport", "shuttle", "route", "hostel bus", "commute", "pickup"],
        "content": (
            "Campus Transportation Details:\n"
            "• Route 1 (Hostel Loop): Departs every 15 minutes between 07:30 AM and 07:30 PM connecting East Hostels to Academic Complex.\n"
            "• Route 2 (City Express): Departs Main Campus Gate at 08:00 AM, 12:30 PM, and 05:30 PM to Metro Central Station.\n"
            "• Route 3 (Night Shuttle): Operates hourly between 08:00 PM and midnight from Library to Residential Blocks."
        ),
        "source_url": "https://campusops.edu/facilities/transport-routes"
    },
    {
        "topic": "dining_hostel",
        "title": "Hostel Dining Hall & Mess Timings",
        "keywords": ["mess", "dining", "food", "canteen", "breakfast", "lunch", "dinner", "hostel meal"],
        "content": (
            "University Dining Hall Operational Hours:\n"
            "• Breakfast: 07:30 AM – 09:30 AM\n"
            "• Lunch: 12:30 PM – 02:30 PM\n"
            "• Evening Tea & Snacks: 05:00 PM – 06:15 PM\n"
            "• Dinner: 07:30 PM – 09:30 PM\n"
            "Special packed meals for students with late examination sessions must be requested 3 hours in advance."
        ),
        "source_url": "https://campusops.edu/student-life/dining-hours"
    },
    {
        "topic": "admin_office_hours",
        "title": "Administrative Offices & Department Contact Hours",
        "keywords": ["admin", "office", "registrar", "accounts", "dean", "student affairs", "working hours"],
        "content": (
            "University Administrative Working Hours:\n"
            "• Registrar & Academic Affairs: Monday to Friday, 09:00 AM – 05:00 PM (Lunch break: 01:00 PM – 02:00 PM).\n"
            "• Facilities Management Office: Open 24/7 for emergency dispatch at Extension 4001.\n"
            "• Student Welfare & Counseling: Monday to Friday, 10:00 AM – 06:00 PM."
        ),
        "source_url": "https://campusops.edu/administration/office-directory"
    }
]

def search_institutional_knowledge(query: str) -> Optional[Dict[str, Any]]:
    """
    Finds the most relevant verified institutional knowledge entry for a user query.
    """
    lower = query.lower()
    best_entry = None
    max_matches = 0

    for entry in INSTITUTIONAL_KNOWLEDGE_ENTRIES:
        matches = sum(1 for kw in entry["keywords"] if kw in lower)
        if matches > max_matches:
            max_matches = matches
            best_entry = entry

    if max_matches >= 1:
        return best_entry

    return None

