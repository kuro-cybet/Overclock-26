from fastapi import APIRouter
from app.api.v1 import (
    auth,
    users,
    incidents,
    reports,
    work_orders,
    staff,
    rooms,
    bookings,
    assets,
    inventory,
    procurement,
    approvals,
    recovery,
    sla,
    notifications,
    analytics,
    simulations,
    integrations,
    intelligence
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(incidents.router)
api_router.include_router(reports.router)
api_router.include_router(work_orders.router)
api_router.include_router(staff.router)
api_router.include_router(rooms.router)
api_router.include_router(bookings.router)
api_router.include_router(assets.router)
api_router.include_router(inventory.router)
api_router.include_router(procurement.router)
api_router.include_router(approvals.router)
api_router.include_router(recovery.router)
api_router.include_router(sla.router)
api_router.include_router(notifications.router)
api_router.include_router(analytics.router)
api_router.include_router(simulations.router)
api_router.include_router(integrations.router)
api_router.include_router(intelligence.router)

