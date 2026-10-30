import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.database.models.asset import Asset
from app.database.models.room import Room
from app.database.models.campus import Building
from app.database.models.maintenance import AssetMaintenanceHistory, PreventiveMaintenanceSchedule
from app.database.models.incident import Incident
from app.database.models.work_order import WorkOrder

class PredictiveMaintenanceService:
    """
    Transparent statistical and rule-based predictive maintenance engine.
    Calculates dynamic asset health scores (0-100), 30-day failure risk probabilities,
    and automated service recommendations using empirical operating parameters.
    """

    # Expected lifespans in years by equipment category
    EXPECTED_LIFESPAN_YEARS = {
        "network": 4.0,
        "hvac": 8.0,
        "electrical": 6.0,
        "av_multimedia": 3.5,
        "plumbing": 10.0,
        "furniture": 7.0,
        "general": 5.0
    }

    def evaluate_asset_health(self, db: Session, asset: Asset) -> Dict[str, Any]:
        """
        Calculates multi-factor transparent health score and risk level for a single asset.
        """
        now = datetime.utcnow()
        category = (asset.category or "general").lower()
        expected_lifespan = self.EXPECTED_LIFESPAN_YEARS.get(category, 5.0)

        # 1. Age Factor (0 - 25 penalty points)
        purchase_date = asset.created_at or (now - timedelta(days=365))
        age_years = max(0.1, (now - purchase_date).total_seconds() / (365.25 * 86400.0))
        age_fraction = min(2.0, age_years / expected_lifespan)
        age_penalty = min(25.0, age_fraction * 15.0)

        # 2. Failure History Penalty (0 - 35 points)
        failure_count = db.query(Incident).filter(Incident.asset_id == asset.id).count()
        failure_penalty = min(35.0, failure_count * 9.0)

        # 3. Corrective Repairs vs. Preventive Maintenance (0 - 20 points)
        maintenance_logs = (
            db.query(AssetMaintenanceHistory)
            .filter(AssetMaintenanceHistory.asset_id == asset.id)
            .all()
        )
        corrective_count = sum(1 for m in maintenance_logs if m.maintenance_type == "corrective")
        preventive_count = sum(1 for m in maintenance_logs if m.maintenance_type == "preventive")
        repair_penalty = min(20.0, corrective_count * 5.0)
        pm_bonus = min(10.0, preventive_count * 3.0)

        # 4. Service Staleness Penalty (0 - 20 points)
        last_serviced = asset.last_inspected_at or (now - timedelta(days=120))
        days_since_service = max(0, (now - last_serviced).days)
        if days_since_service > 365:
            staleness_penalty = 20.0
        elif days_since_service > 180:
            staleness_penalty = 12.0
        elif days_since_service > 90:
            staleness_penalty = 5.0
        else:
            staleness_penalty = 0.0

        # Calculate final composite score
        raw_score = 100.0 - (age_penalty + failure_penalty + repair_penalty + staleness_penalty) + pm_bonus
        health_score = int(max(5, min(100, round(raw_score))))

        # Classify Failure Risk Level
        if health_score >= 75:
            risk_level = "Healthy"
            risk_color = "emerald"
        elif health_score >= 50:
            risk_level = "Attention Required"
            risk_color = "amber"
        else:
            risk_level = "High Risk"
            risk_color = "rose"

        # Projected 30-Day Failure Probability (Empirical Poisson / Hazard estimate)
        # Higher failure count and staleness exponentially elevate failure likelihood
        lambda_rate = (0.05 + (failure_count * 0.08) + (staleness_penalty * 0.015)) * (1.0 + age_fraction * 0.4)
        failure_prob_30d = round(min(0.96, max(0.02, 1.0 - math.exp(-lambda_rate))), 3)

        # Tailored Recommendation
        recommendations = self._generate_recommendation(
            category=category,
            health_score=health_score,
            days_since_service=days_since_service,
            failure_count=failure_count
        )

        return {
            "asset_id": asset.id,
            "asset_tag": asset.asset_tag,
            "name": asset.name,
            "category": category,
            "health_score": health_score,
            "risk_level": risk_level,
            "risk_color": risk_color,
            "failure_probability_30d": failure_prob_30d,
            "metrics": {
                "age_years": round(age_years, 1),
                "expected_lifespan_years": expected_lifespan,
                "days_since_service": days_since_service,
                "failure_count": failure_count,
                "corrective_repairs": corrective_count,
                "preventive_services": preventive_count,
            },
            "score_breakdown": {
                "base": 100,
                "age_penalty": round(age_penalty, 1),
                "failure_penalty": round(failure_penalty, 1),
                "repair_penalty": round(repair_penalty, 1),
                "staleness_penalty": round(staleness_penalty, 1),
                "pm_bonus": round(pm_bonus, 1),
            },
            "recommended_action": recommendations["action"],
            "urgency": recommendations["urgency"],
            "suggested_parts": recommendations["parts"]
        }

    def _generate_recommendation(
        self,
        category: str,
        health_score: int,
        days_since_service: int,
        failure_count: int
    ) -> Dict[str, Any]:
        if health_score < 50:
            urgency = "immediate"
            if category == "network":
                action = "Replace degraded network switch port module; run loopback diagnostics."
                parts = ["SFP+ Transceiver Module", "CAT6 Patch Cables"]
            elif category == "hvac":
                action = "Overhaul compressor motor; flush refrigerant lines and inspect thermostat valve."
                parts = ["HVAC Filter Pack", "Thermostatic Expansion Valve"]
            elif category == "av_multimedia":
                action = "Replace projector optical lamp engine & clean particulate filters."
                parts = ["OEM Projector Lamp Unit", "HDMI Extender Receiver"]
            elif category == "electrical":
                action = "Perform emergency circuit breaker thermal scan and replace worn contactors."
                parts = ["20A Circuit Breaker", "Surge Protector Outlet"]
            else:
                action = "Immediate physical overhaul and complete safety diagnostics."
                parts = ["Universal Hardware Kit"]
        elif health_score < 75:
            urgency = "scheduled"
            if days_since_service > 180:
                action = f"Perform semi-annual preventive calibration and cleaning ({days_since_service} days unserviced)."
            else:
                action = "Inspect physical fittings, power draw, and firmware logs during next routine sweep."
            parts = ["Filter Element", "Cleaning Solvent & Lubricant"]
        else:
            urgency = "routine"
            action = "Nominal operation. Continue standard preventive maintenance cycle."
            parts = []

        return {"action": action, "urgency": urgency, "parts": parts}

    def get_fleet_predictive_overview(self, db: Session) -> Dict[str, Any]:
        """
        Scans all assets across the university and produces tiered predictive maintenance queues.
        """
        assets = db.query(Asset).all()

        healthy = []
        attention = []
        high_risk = []

        for a in assets:
            eval_res = self.evaluate_asset_health(db, a)
            
            # Enrich with room and building details
            room = db.query(Room).filter(Room.id == a.room_id).first()
            building = db.query(Building).filter(Building.id == room.building_id).first() if room else None
            eval_res["location"] = f"{building.name if building else 'Campus'} - {room.room_number if room else 'Storage'}"

            if eval_res["risk_level"] == "High Risk":
                high_risk.append(eval_res)
            elif eval_res["risk_level"] == "Attention Required":
                attention.append(eval_res)
            else:
                healthy.append(eval_res)

        # Fetch upcoming PM schedules
        now = datetime.utcnow()
        upcoming_pm = (
            db.query(PreventiveMaintenanceSchedule)
            .filter(PreventiveMaintenanceSchedule.is_active == True)
            .order_by(PreventiveMaintenanceSchedule.next_due_at.asc())
            .limit(10)
            .all()
        )

        pm_items = []
        for s in upcoming_pm:
            asset = db.query(Asset).filter(Asset.id == s.asset_id).first()
            if asset:
                pm_items.append({
                    "schedule_id": s.id,
                    "asset_id": asset.id,
                    "asset_tag": asset.asset_tag,
                    "asset_name": asset.name,
                    "frequency_days": s.frequency_days,
                    "next_due_at": s.next_due_at.strftime("%Y-%m-%d") if s.next_due_at else "Pending",
                    "days_remaining": (s.next_due_at - now).days if s.next_due_at else 0
                })

        return {
            "summary": {
                "total_assets": len(assets),
                "healthy_count": len(healthy),
                "attention_count": len(attention),
                "high_risk_count": len(high_risk),
                "upcoming_pm_count": len(pm_items)
            },
            "high_risk_assets": sorted(high_risk, key=lambda x: x["health_score"]),
            "attention_required_assets": sorted(attention, key=lambda x: x["health_score"]),
            "healthy_assets": sorted(healthy, key=lambda x: x["health_score"], reverse=True)[:15],
            "upcoming_schedules": pm_items
        }

predictive_maintenance_service = PredictiveMaintenanceService()
