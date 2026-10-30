import json
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.database.models.report import Report
from app.database.models.incident import Incident
from app.database.models.campus import Building
from app.database.models.room import Room
from app.database.models.asset import Asset
from app.services.ai_service import ai_service
from app.services import workflow_notifications
from app.core.exceptions import CampusOpsException

class IntakeService:
    def process_incoming_report(
        self,
        db: Session,
        reporter_id: str,
        reporter_role: str,
        title: str,
        description: str,
        building_id: Optional[str] = None,
        room_id: Optional[str] = None,
        asset_id: Optional[str] = None,
        category: Optional[str] = None,
        urgency: Optional[str] = None,
        source: str = "web_portal",
        reporter_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        # 1. Run AI Extraction
        full_text = f"{title}. {description}"
        ai_extraction = ai_service.extract_incident_entities(full_text)

        # 2. Deterministic entity resolution & validation
        resolved_building_id = building_id
        resolved_room_id = room_id
        resolved_asset_id = asset_id

        # Resolve building if omitted but detected
        if not resolved_building_id and ai_extraction["location_building"]:
            b = db.query(Building).filter(Building.name.ilike(f"%{ai_extraction['location_building']}%")).first()
            if b:
                resolved_building_id = b.id

        # Resolve room if omitted but detected
        if not resolved_room_id and ai_extraction["location_room"]:
            r = db.query(Room).filter(Room.name.ilike(f"%{ai_extraction['location_room']}%")).first()
            if r:
                resolved_room_id = r.id
                if not resolved_building_id:
                    resolved_building_id = r.building_id

        # Fallback to first building if still unresolved
        if not resolved_building_id:
            first_b = db.query(Building).first()
            resolved_building_id = first_b.id if first_b else None

        # Resolve asset if omitted
        if not resolved_asset_id and resolved_room_id:
            asset = db.query(Asset).filter(Asset.room_id == resolved_room_id).first()
            if asset:
                resolved_asset_id = asset.id

        # 3. Policy-based urgency & priority determination
        final_category = category or ai_extraction["category"]
        final_urgency = urgency or ai_extraction["urgency"]

        # Map to Incident Priority (P1 to P4)
        priority_map = {
            "critical": "P1",
            "high": "P2",
            "medium": "P3",
            "low": "P4"
        }
        computed_priority = priority_map.get(final_urgency, "P3")

        # 4. Check for existing active incident in the exact room/category
        existing_incident = None
        if resolved_room_id:
            existing_incident = db.query(Incident).filter(
                Incident.room_id == resolved_room_id,
                Incident.category == final_category,
                Incident.status.in_(["open", "in_progress", "pending_parts"])
            ).first()

        # 5. Persist the Report
        report_count = db.query(Report).count()
        report_code = f"RPT-{datetime_suffix()}-{report_count + 1:04d}"

        report = Report(
            report_code=report_code,
            title=title,
            description=description,
            category=final_category,
            urgency=final_urgency,
            building_id=resolved_building_id,
            room_id=resolved_room_id,
            asset_id=resolved_asset_id,
            reporter_id=reporter_id,
            reporter_role=reporter_role,
            source=source,
            status="correlated" if existing_incident else "submitted",
            incident_id=existing_incident.id if existing_incident else None,
            ai_extracted_meta=json.dumps(ai_extraction)
        )
        db.add(report)
        db.flush()

        # If duplicate matched to existing incident, increment correlation count
        if existing_incident:
            existing_incident.correlated_count += 1
            existing_incident.summary = f"Aggregated {existing_incident.correlated_count} reports for {existing_incident.category} issue."
            db.flush()

        # Acknowledge the reporter (in-app + email) and alert the facilities desk
        # when the report still needs triage.  The caller commits the transaction.
        reporter_outbox = workflow_notifications.report_submitted(
            db, report, reporter_email=reporter_email
        )

        return {
            "report": report,
            "ai_extraction": ai_extraction,
            "matched_existing_incident": existing_incident is not None,
            "incident_id": existing_incident.id if existing_incident else None,
            "outbox_id": reporter_outbox.id if reporter_outbox else None,
        }

def datetime_suffix():
    from datetime import datetime
    return datetime.utcnow().strftime("%Y%m")

intake_service = IntakeService()
