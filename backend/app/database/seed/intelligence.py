import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.models.intelligence import HistoricalResolution

HISTORICAL_CASES = [
    {
        "category": "network",
        "symptoms": "Wi-Fi access point SSID not broadcasting in Computer Lab, authentication timeouts",
        "diagnosis": "PoE injector voltage dip caused radio card crash on access point",
        "action_taken": "Power cycled PoE switch port, re-terminated Cat6A RJ45 plug and reloaded firmware",
        "parts_used": json.dumps(["Cat6A Patch Cable", "RJ45 Modular Plug"]),
        "resolution_duration_minutes": 35,
        "verified_outcome": "Radio channels restored, sustained 450Mbps throughput verified"
    },
    {
        "category": "classroom",
        "symptoms": "Projector displaying purple tint and turning off after 5 minutes",
        "diagnosis": "Laser optical ballast overheating due to clogged intake mesh filter",
        "action_taken": "Cleaned air intake filter, replaced high-output laser projector lamp module",
        "parts_used": json.dumps(["Laser Projector Bulb"]),
        "resolution_duration_minutes": 45,
        "verified_outcome": "Color balance calibrated, full lumen output verified"
    },
    {
        "category": "electrical",
        "symptoms": "Tripped miniature circuit breaker on bench line during multi-laptop charging",
        "diagnosis": "Loose terminal connection causing localized thermal overload at 28A",
        "action_taken": "Torqued neutral busbar connections and swapped MCB 32A breaker",
        "parts_used": json.dumps(["Miniature Circuit Breaker 32A"]),
        "resolution_duration_minutes": 50,
        "verified_outcome": "Load test passed with 30 concurrent workstations at normal temperature"
    },
    {
        "category": "cleanliness",
        "symptoms": "Restroom sensor tap running water continuously across main aisle",
        "diagnosis": "Infrared optical sensor scratched and solenoid plunger stuck open",
        "action_taken": "Replaced solenoid sensor valve diaphragm and recalibrated detection range",
        "parts_used": json.dumps(["Touchless Tap Sensor Valve"]),
        "resolution_duration_minutes": 25,
        "verified_outcome": "Water shutoff confirmed within 2 seconds of hands removal"
    }
]

def seed_intelligence(db: Session):
    for h in HISTORICAL_CASES:
        res = HistoricalResolution(
            category=h["category"],
            symptoms=h["symptoms"],
            diagnosis=h["diagnosis"],
            action_taken=h["action_taken"],
            parts_used=h["parts_used"],
            resolution_duration_minutes=h["resolution_duration_minutes"],
            verified_outcome=h["verified_outcome"]
        )
        db.add(res)
    db.flush()

