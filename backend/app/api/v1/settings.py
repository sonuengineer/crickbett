from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserArbSettings
from app.schemas.cricket import ArbSettingsResponse, ArbSettingsUpdate

router = APIRouter(prefix="/cricket/settings", tags=["settings"])


@router.get("/", response_model=ArbSettingsResponse)
async def get_arb_settings(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(UserArbSettings).where(UserArbSettings.user_id == user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        # Create default settings
        settings = UserArbSettings(user_id=user.id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings


@router.put("/", response_model=ArbSettingsResponse)
async def update_arb_settings(
    request: ArbSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(UserArbSettings).where(UserArbSettings.user_id == user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = UserArbSettings(user_id=user.id)
        db.add(settings)

    # Update only provided fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)
    return settings
