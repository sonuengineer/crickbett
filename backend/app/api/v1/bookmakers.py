from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.cricket import Bookmaker
from app.schemas.cricket import BookmakerResponse

router = APIRouter(prefix="/cricket/bookmakers", tags=["bookmakers"])


@router.get("/", response_model=list[BookmakerResponse])
async def list_bookmakers(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all registered bookmakers."""
    result = await db.execute(
        select(Bookmaker).order_by(Bookmaker.name)
    )
    return result.scalars().all()
