from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.bookmakers import router as bookmakers_router
from app.api.v1.matches import router as matches_router
from app.api.v1.odds import router as odds_router
from app.api.v1.arb import router as arb_router
from app.api.v1.positions import router as positions_router
from app.api.v1.settings import router as settings_router
from app.api.v1.capture import router as capture_router
from app.api.v1.hedge_monitor import router as hedge_monitor_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(bookmakers_router)
api_v1_router.include_router(matches_router)
api_v1_router.include_router(odds_router)
api_v1_router.include_router(arb_router)
api_v1_router.include_router(positions_router)
api_v1_router.include_router(settings_router)
api_v1_router.include_router(capture_router)
api_v1_router.include_router(hedge_monitor_router)
