from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.simulations.exam_room_unavailable import exam_room_sim
from app.simulations.technician_absence import technician_absence_sim
from app.simulations.stock_shortage import stock_shortage_sim
from app.simulations.wifi_outage import wifi_outage_sim
from app.database.seed.seed import reset_and_seed
from app.api.deps import require_role, require_admin_sub_role
from app.database.models.user import User

router = APIRouter(prefix="/simulations", tags=["simulations"])

# Only system_admin can reset or run simulations
_sim_guard = require_admin_sub_role(["system_admin"])

@router.post("/reset")
def reset_simulation_state(current_user: User = Depends(_sim_guard)):
    """Restores the baseline seed state cleanly without leaving orphaned records."""
    reset_and_seed(verbose=False)
    return {"status": "success", "message": "Baseline university seed data restored cleanly."}

@router.post("/{scenario}")
def trigger_simulation(
    scenario: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(_sim_guard),
):
    if scenario in ["exam_room_unavailable", "examination_room_unavailable"]:
        result = exam_room_sim.trigger(db)
        db.commit()
        return result
    elif scenario in ["technician_unavailable", "technician_absence"]:
        result = technician_absence_sim.trigger(db)
        db.commit()
        return result
    elif scenario in ["stock_shortage", "critical_part_out_of_stock"]:
        result = stock_shortage_sim.trigger(db)
        db.commit()
        return result
    elif scenario in ["wifi_outage", "multiple_wifi_complaints"]:
        result = wifi_outage_sim.trigger(db)
        db.commit()
        return result
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown simulation scenario '{scenario}'. Valid options: exam_room_unavailable, technician_unavailable, stock_shortage, wifi_outage"
        )

