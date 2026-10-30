import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.database.models.intelligence import HistoricalResolution, PredictiveAlert
from app.database.models.incident import Incident
from app.database.models.inventory import InventoryItem
from app.database.models.room import Room

class HistoricalIntelligenceService:
    def retrieve_similar_cases(
        self,
        db: Session,
        category: str,
        symptom_text: str,
        room_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = db.query(HistoricalResolution).filter(HistoricalResolution.category == category)
        cases = query.all()
        
        results = []
        lower_symptom = symptom_text.lower()
        
        for c in cases:
            # Score similarity
            score = 60
            if any(term in lower_symptom for term in c.symptoms.lower().split()):
                score += 25
            if room_id and c.room_id == room_id:
                score += 15

            results.append({
                "id": c.id,
                "category": c.category,
                "symptoms": c.symptoms,
                "diagnosis": c.diagnosis,
                "action_taken": c.action_taken,
                "parts_used": json.loads(c.parts_used) if c.parts_used else [],
                "resolution_duration_minutes": c.resolution_duration_minutes,
                "verified_outcome": c.verified_outcome,
                "similarity_score": min(98, score),
                "confidence_label": "High Confidence" if score >= 80 else "Moderate Context"
            })

        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:4]

class PredictiveAlertsService:
    def evaluate_predictive_alerts(self, db: Session) -> List[Dict[str, Any]]:
        alerts = []
        now = datetime.utcnow()

        # 1. Predictive SLA At-Risk Alerts
        active_incidents = db.query(Incident).filter(
            Incident.status.in_(["open", "in_progress", "pending_parts"])
        ).all()
        for inc in active_incidents:
            if inc.sla_due_at:
                diff_mins = (inc.sla_due_at - now).total_seconds() / 60.0
                if 0 < diff_mins <= 90 and not inc.is_sla_breached:
                    key = f"sla_risk_{inc.id}_{now.strftime('%Y%m%d')}"
                    alerts.append({
                        "alert_type": "sla_risk",
                        "affected_entity_type": "incident",
                        "affected_entity_id": inc.id,
                        "title": f"Predicted SLA Breach: {inc.incident_code}",
                        "evidence_refs": f"Incident has {round(diff_mins)} minutes remaining before resolution target breaches.",
                        "trigger_threshold": "Less than 90m to SLA deadline",
                        "predicted_window": f"Within next {round(diff_mins)} mins",
                        "confidence": 0.92,
                        "status": "active",
                        "deduplication_key": key,
                        "recommended_action": f"Elevate priority or reassign additional field technician to {inc.incident_code} immediately."
                    })

        # 2. Critical Stock Shortage Alerts
        items = db.query(InventoryItem).all()
        for it in items:
            avail = it.stock_quantity - it.reserved_quantity
            if avail <= 1:
                key = f"stock_shortage_{it.id}_{now.strftime('%Y%m%d')}"
                alerts.append({
                    "alert_type": "stock_shortage",
                    "affected_entity_type": "item",
                    "affected_entity_id": it.id,
                    "title": f"Inventory Depletion Risk: {it.name}",
                    "evidence_refs": f"Available quantity ({avail}) is below safety threshold ({it.minimum_threshold}).",
                    "trigger_threshold": "Available units <= 1",
                    "predicted_window": "Imminent for next work order",
                    "confidence": 0.95,
                    "status": "active",
                    "deduplication_key": key,
                    "recommended_action": f"Generate emergency purchase requisition for 5x {it.name}."
                })

        # 3. Room Readiness Gaps
        stale_rooms = db.query(Room).filter(Room.daily_readiness_status.in_(["stale", "unconfirmed"])).all()
        if len(stale_rooms) > 5:
            key = f"readiness_gap_campus_{now.strftime('%Y%m%d')}"
            alerts.append({
                "alert_type": "readiness_gap",
                "affected_entity_type": "room",
                "affected_entity_id": "all",
                "title": f"Campus-wide Room Readiness Gap ({len(stale_rooms)} rooms)",
                "evidence_refs": f"{len(stale_rooms)} educational spaces lack confirmed daily inspection.",
                "trigger_threshold": "Stale/Unconfirmed rooms > 5",
                "predicted_window": "Prior to 09:00 AM lectures",
                "confidence": 0.88,
                "status": "active",
                "deduplication_key": key,
                "recommended_action": "Dispatch Floor Incharges for morning equipment checks."
            })

        # Persist / Upsert into DB
        for a in alerts:
            existing = db.query(PredictiveAlert).filter(PredictiveAlert.deduplication_key == a["deduplication_key"]).first()
            if not existing:
                pa = PredictiveAlert(**a)
                db.add(pa)
        db.flush()

        all_active = db.query(PredictiveAlert).filter(PredictiveAlert.status == "active").order_by(PredictiveAlert.created_at.desc()).limit(15).all()
        return [
            {
                "id": p.id,
                "alert_type": p.alert_type,
                "title": p.title,
                "evidence_refs": p.evidence_refs,
                "trigger_threshold": p.trigger_threshold,
                "predicted_window": p.predicted_window,
                "confidence": p.confidence,
                "status": p.status,
                "recommended_action": p.recommended_action,
                "created_at": p.created_at.isoformat()
            }
            for p in all_active
        ]

historical_intelligence_service = HistoricalIntelligenceService()
predictive_alerts_service = PredictiveAlertsService()

