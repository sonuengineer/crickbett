from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.cricket import OddsSnapshot, Bookmaker
from app.schemas.cricket import OddsResponse, OddsComparisonItem

router = APIRouter(prefix="/cricket/odds", tags=["odds"])


@router.get("/{match_id}", response_model=list[OddsResponse])
async def get_match_odds(
    match_id: UUID,
    market_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get latest odds for a match, optionally filtered by market type."""
    query = (
        select(OddsSnapshot)
        .options(joinedload(OddsSnapshot.bookmaker))
        .where(OddsSnapshot.match_id == match_id)
        .order_by(desc(OddsSnapshot.scraped_at))
        .limit(200)
    )
    if market_type:
        query = query.where(OddsSnapshot.market_type == market_type)

    result = await db.execute(query)
    snapshots = result.unique().scalars().all()

    # Populate bookmaker_name for response
    return [
        OddsResponse(
            id=s.id,
            match_id=s.match_id,
            bookmaker_id=s.bookmaker_id,
            bookmaker_name=s.bookmaker.name if s.bookmaker else None,
            market_type=s.market_type,
            selection=s.selection,
            odds_decimal=float(s.odds_decimal),
            odds_original=s.odds_original,
            is_back=s.is_back,
            lay_odds=float(s.lay_odds) if s.lay_odds else None,
            available_volume=float(s.available_volume) if s.available_volume else None,
            scraped_at=s.scraped_at,
            is_live=s.is_live,
        )
        for s in snapshots
    ]


@router.get("/{match_id}/comparison")
async def get_odds_comparison(
    match_id: UUID,
    market_type: str = Query("match_winner"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[OddsComparisonItem]:
    """Side-by-side odds comparison across bookmakers for a specific market."""
    # Get latest odds per bookmaker per selection (using subquery for latest)
    query = (
        select(OddsSnapshot)
        .options(joinedload(OddsSnapshot.bookmaker))
        .where(OddsSnapshot.match_id == match_id)
        .where(OddsSnapshot.market_type == market_type)
        .where(OddsSnapshot.is_back == True)
        .order_by(desc(OddsSnapshot.scraped_at))
    )

    result = await db.execute(query)
    snapshots = result.scalars().all()

    # Group by selection, keep latest per bookmaker
    comparison: dict[str, dict[str, float]] = {}
    seen: set[tuple[str, str]] = set()

    for snap in snapshots:
        bk_name = snap.bookmaker.name if snap.bookmaker else "unknown"
        key = (snap.selection, bk_name)
        if key in seen:
            continue
        seen.add(key)

        if snap.selection not in comparison:
            comparison[snap.selection] = {}
        comparison[snap.selection][bk_name] = float(snap.odds_decimal)

    items = []
    for selection, bk_odds in comparison.items():
        best_bk = max(bk_odds, key=bk_odds.get)
        items.append(OddsComparisonItem(
            selection=selection,
            bookmaker_odds=bk_odds,
            best_bookmaker=best_bk,
            best_odds=bk_odds[best_bk],
        ))

    return items


@router.get("/{match_id}/history")
async def get_odds_history(
    match_id: UUID,
    selection: str = Query(...),
    market_type: str = Query("match_winner"),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[OddsResponse]:
    """Historical odds timeline for a specific selection."""
    result = await db.execute(
        select(OddsSnapshot)
        .where(OddsSnapshot.match_id == match_id)
        .where(OddsSnapshot.selection == selection)
        .where(OddsSnapshot.market_type == market_type)
        .order_by(OddsSnapshot.scraped_at)
        .limit(limit)
    )
    return result.scalars().all()
