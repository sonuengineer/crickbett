from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.cricket import ArbitrageOpportunity
from app.schemas.cricket import ArbResponse

router = APIRouter(prefix="/cricket/arb", tags=["arbitrage"])


@router.get("/active", response_model=list[ArbResponse])
async def list_active_arbs(
    arb_type: str | None = Query(None, description="cross_book, back_lay, live_swing"),
    min_profit: float | None = Query(None, description="Minimum profit %"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all currently active arbitrage opportunities."""
    query = (
        select(ArbitrageOpportunity)
        .where(ArbitrageOpportunity.status == "active")
        .order_by(desc(ArbitrageOpportunity.profit_pct))
    )

    if arb_type:
        query = query.where(ArbitrageOpportunity.arb_type == arb_type)
    if min_profit is not None:
        query = query.where(ArbitrageOpportunity.profit_pct >= min_profit)

    result = await db.execute(query.limit(50))
    return result.scalars().all()


@router.get("/history", response_model=list[ArbResponse])
async def list_arb_history(
    arb_type: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get historical arbitrage opportunities."""
    query = (
        select(ArbitrageOpportunity)
        .order_by(desc(ArbitrageOpportunity.detected_at))
    )

    if arb_type:
        query = query.where(ArbitrageOpportunity.arb_type == arb_type)

    result = await db.execute(query.limit(limit))
    return result.scalars().all()


@router.get("/{arb_id}", response_model=ArbResponse)
async def get_arb(
    arb_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ArbitrageOpportunity).where(ArbitrageOpportunity.id == arb_id)
    )
    arb = result.scalar_one_or_none()
    if not arb:
        raise HTTPException(status_code=404, detail="Arbitrage opportunity not found")
    return arb


@router.post("/{arb_id}/dismiss")
async def dismiss_arb(
    arb_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ArbitrageOpportunity).where(ArbitrageOpportunity.id == arb_id)
    )
    arb = result.scalar_one_or_none()
    if not arb:
        raise HTTPException(status_code=404, detail="Not found")

    arb.status = "dismissed"
    await db.commit()
    return {"message": "Arb dismissed"}
