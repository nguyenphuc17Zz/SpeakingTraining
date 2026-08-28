from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.settings.models import UserSettings
from app.domains.settings.schemas import UserSettingsUpdate
from app.domains.users.service import UserService


class SettingsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_service = UserService(session)

    async def get_or_create_settings(self, user_id: str | None = None) -> UserSettings:
        if not user_id:
            user = await self.user_service.get_or_create_default_user()
            user_id = user.id

        result = await self.session.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()
        if not settings:
            settings = UserSettings(
                user_id=user_id,
                theme="system",
                language="ja",
                timezone="Asia/Tokyo",
                default_ai_provider="gemini",
                default_ai_model="gemini-1.5-flash",
                default_tts_provider="voicevox",
                default_stt_provider="whisper_local",
            )
            self.session.add(settings)
            await self.session.commit()
            await self.session.refresh(settings)
        return settings

    async def update_settings(self, payload: UserSettingsUpdate, user_id: str | None = None) -> UserSettings:
        settings = await self.get_or_create_settings(user_id)
        update_data = payload.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            setattr(settings, key, val)
        await self.session.commit()
        await self.session.refresh(settings)
        return settings
