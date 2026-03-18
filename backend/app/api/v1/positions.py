from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.cricket import HedgePosition
from app.schemas.cricket import PositionCreate, PositionHedge, PositionResponse
from app.services.hedge_calculator import calculate_hedge

router = APIRouter(prefix="/cricket/positions", tags=["positions"])


@router.get("/", response_model=list[PositionResponse])
async def list_positions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(HedgePosition)
        .where(HedgePosition.user_id == user.id)
        .order_by(HedgePosition.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=PositionResponse)
async def create_position(
    request: PositionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Record a new initial bet (before hedging)."""
    position = HedgePosition(
        user_id=user.id,
        match_id=request.match_id,
        market_type=request.market_type,
        initial_bet_bookmaker=request.initial_bet_bookmaker,
        initial_bet_selection=request.initial_bet_selection,
        initial_bet_odds=request.initial_bet_odds,
        initial_bet_stake=request.initial_bet_stake,
        notes=request.notes,
        position_status="open",
    )
    db.add(position)
    await db.commit()
    await db.refresh(position)
    return position


@router.put("/{position_id}/hedge", response_model=PositionResponse)
async def record_hedge(
    position_id: UUID,
    request: PositionHedge,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Record the hedge leg and compute guaranteed profit."""
    result = await db.execute(
        select(HedgePosition)
        .where(HedgePosition.id == position_id)
        .where(HedgePosition.user_id == user.id)
    )
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    # Calculate guaranteed profit
    calc = calculate_hedge(
        original_odds=float(position.initial_bet_odds),
        original_stake=float(position.initial_bet_stake),
        current_odds_opposite=request.hedge_bet_odds,
    )

    position.hedge_bet_bookmaker = request.hedge_bet_bookmaker
    position.hedge_bet_selection = request.hedge_bet_selection
    position.hedge_bet_odds = request.hedge_bet_odds
    position.hedge_bet_stake = request.hedge_bet_stake
    position.guaranteed_profit = calc.guaranteed_profit
    position.position_status = "partially_hedged"

    await db.commit()
    await db.refresh(position)
    return position


@router.put("/{position_id}/close", response_model=PositionResponse)
async def close_position(
    position_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mark position as closed."""
    result = await db.execute(
        select(HedgePosition)
        .where(HedgePosition.id == position_id)
        .where(HedgePosition.user_id == user.id)
    )
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    position.position_status = "closed"
    await db.commit()
    await db.refresh(position)
    return position
