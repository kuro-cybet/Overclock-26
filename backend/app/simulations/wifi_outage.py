import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database.models.room import Room
from app.database.models.user import User
from app.services.intake_service import intake_service
from app.services.correlation_service import correlation_service
from app.database.models.audit import AuditLog

class WifiOutageSimulation:
    def trigger(self, db: Session, room_name: str = "Computer Lab A") -> Dict[str, Any]:
        room = db.query(Room).filter(Room.name.ilike(f"%{room_name}%")).first()
        if not room:
            room = db.query(Room).first()

        students = db.query(User).filter(User.role == "student").limit(5).all()

        complaint_texts = [
            "Wi-Fi isn't working in Computer Lab A. We have an exam in 30 minutes.",
            "Can't connect to eduroam wireless network in Lab A. Signal is gone.",
            "Internet dropped completely across all computers in Computer Lab A.",
            "Wi-Fi AP blinking red in Lab A, nobody can submit their assignment."
        ]

        submitted_report_ids = []
        for idx, text in enumerate(complaint_texts):
            student = students[idx % len(students)]
            result = intake_service.process_incoming_report(
                db=db,
                reporter_id=student.id,
                reporter_role="student",
                title=f"Lab A Network Failure - Report #{idx+1}",
                description=text,
                building_id=room.building_id,
                room_id=room.id,
                category="network",
                urgency="critical",
                source="web_portal"
            )
            submitted_report_ids.append(result["report"].id)

        # Correlate all reports into one canonical incident
        canonical_incident = correlation_service.correlate_reports_to_incident(
            db=db,
            report_ids=submitted_report_ids,
            canonical_title=f"Major Outage: Engineering Wi-Fi AP Offline in {room.name}",
            actor_id="admin-sim",
            actor_role="admin"
        )

        after_state = {
            "incident_code": canonical_incident.incident_code,
            "incident_title": canonical_incident.title,
            "priority": canonical_incident.priority,
            "status": canonical_incident.status,
            "correlated_reports_count": len(submitted_report_ids),
            "affected_room": room.name,
            "reports": submitted_report_ids
        }

        # Audit
        audit = AuditLog(
            action="SIMULATION_WIFI_OUTAGE",
            actor_id="admin-sim",
            actor_role="admin",
            entity_type="incident",
            entity_id=canonical_incident.id,
            new_value=json.dumps(after_state),
            reason="Scenario Simulator: Multiple Wi-Fi complaints correlated into canonical outage"
        )
        db.add(audit)
        db.flush()

        return {
            "scenario": "multiple_wifi_complaints",
            "summary": f"Simulated 4 student reports for {room.name}. Successfully correlated into single canonical incident {canonical_incident.incident_code}.",
            "canonical_incident": after_state,
            "individual_reports_preserved": True
        }

wifi_outage_sim = WifiOutageSimulation()

