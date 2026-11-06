"""API routers aggregated into a single router."""

from fastapi import APIRouter

from . import events, health, radius, stats, system, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(events.router, prefix="/api")
api_router.include_router(stats.router, prefix="/api")
api_router.include_router(radius.router, prefix="/api")
api_router.include_router(system.router, prefix="/api")
api_router.include_router(users.router, prefix="/api")

__all__ = ["api_router"]
