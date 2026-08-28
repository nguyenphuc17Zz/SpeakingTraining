from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, get_settings_service
from app.domains.settings.schemas import UserSettingsRead, UserSettingsUpdate
from app.domains.settings.service import SettingsService
from app.domains.users.models import User

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=UserSettingsRead, summary="Get User Settings")
async def get_settings(
    current_user: User = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service),
):
    settings = await service.get_or_create_settings(user_id=current_user.id)
    return settings


@router.patch("", response_model=UserSettingsRead, summary="Update User Settings")
async def update_settings(
    payload: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service),
):
    settings = await service.update_settings(payload=payload, user_id=current_user.id)
    return settings
