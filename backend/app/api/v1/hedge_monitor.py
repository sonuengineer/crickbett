"""
Live Hedge Monitor API

User flow:
1. POST /hedge-monitor/ → Record pre-match bet
2. GET  /hedge-monitor/ → See all your bets + current hedge opportunities
3. GET  /hedge-monitor/{id} → Single bet + hedge detail
4. POST /hedge-monitor/{id}/hedged → Mark as hedged (you placed the hedge bet)
5. DELETE /hedge-monitor/{id} → Remove a monitor
"""

from fastapi import APIRouter, Depends, HTTPException

from app.core.redis import get_redis
from app.api.deps import get_current_user
from app.models.user import User
from app.services.hedge_monitor import HedgeMonitor
from app.schemas.cricket import (
    HedgeMonitorCreate,
    HedgeMonitorResponse,
)

router = APIRouter(prefix="/cricket/hedge-monitor", tags=["hedge-monitor"])


@router.post("/", response_model=HedgeMonitorResponse)
async def create_hedge_monitor(
    bet: HedgeMonitorCreate,
    user: User = Depends(get_current_user),
):
    """
    Record your pre-match bet. System will monitor live odds
    and alert you when a profitable hedge opportunity appears.

    Example:
        match_team_a: "India"
        match_team_b: "Australia"
        bookmaker: "bet365"
        selection: "India"
        odds: 2.50
        stake: 1000
    """
    redis = await get_redis()
    monitor = HedgeMonitor(redis)
    return await monitor.create_monitor(str(user.id), bet)


@router.get("/", response_model=list[HedgeMonitorResponse])
async def list_hedge_monitors(
    user: User = Depends(get_current_user),
):
    """Get all your monitored bets with current hedge opportunities."""
    redis = await get_redis()
    monitor = HedgeMonitor(redis)
    return await monitor.get_user_monitors(str(user.id))


@router.get("/{monitor_id}", response_model=HedgeMonitorResponse)
async def get_hedge_monitor(
    monitor_id: str,
    user: User = Depends(get_current_user),
):
    """Get a specific bet monitor with live hedge calculation."""
    redis = await get_redis()
    monitor = HedgeMonitor(redis)
    result = await monitor.get_monitor(monitor_id)
    if not result:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return result


@router.post("/{monitor_id}/hedged", response_model=HedgeMonitorResponse)
async def mark_as_hedged(
    monitor_id: str,
    user: User = Depends(get_current_user),
):
    """Mark a monitor as hedged (you placed the hedge bet)."""
    redis = await get_redis()
    monitor = HedgeMonitor(redis)
    result = await monitor.mark_hedged(monitor_id)
    if not result:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return result


@router.delete("/{monitor_id}")
async def delete_hedge_monitor(
    monitor_id: str,
    user: User = Depends(get_current_user),
):
    """Remove a bet monitor."""
    redis = await get_redis()
    monitor = HedgeMonitor(redis)
    await monitor.delete_monitor(monitor_id, str(user.id))
    return {"message": "Monitor deleted"}
