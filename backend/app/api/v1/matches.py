from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.cricket import CricketMatch
from app.schemas.cricket import MatchResponse

router = APIRouter(prefix="/cricket/matches", tags=["matches"])


@router.get("/", response_model=list[MatchResponse])
async def list_matches(
    status: str | None = Query(None, description="Filter: upcoming, live, completed"),
    format: str | None = Query(None, description="Filter: T20, ODI, TEST"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(CricketMatch).order_by(CricketMatch.start_time.desc())

    if status:
        query = query.where(CricketMatch.match_status == status)
    if format:
        query = query.where(CricketMatch.format == format)

    result = await db.execute(query.limit(100))
    return result.scalars().all()


@router.get("/live", response_model=list[MatchResponse])
async def list_live_matches(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CricketMatch)
        .where(CricketMatch.match_status == "live")
        .order_by(CricketMatch.start_time.desc())
    )
    return result.scalars().all()


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CricketMatch).where(CricketMatch.id == match_id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match
