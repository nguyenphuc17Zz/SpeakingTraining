from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.router import AIRouter
from app.domains.ai.service import AIRoutingService, AIUsageService
from app.domains.personas.service import PersonaService
from app.domains.providers.service import CredentialService
from app.domains.settings.service import SettingsService
from app.domains.users.models import User
from app.domains.users.service import UserService
from app.infrastructure.database.session import get_db


async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    """Returns the active user context (defaults to local primary user in Phase 1)."""
    user_service = UserService(db)
    return await user_service.get_or_create_default_user()


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


async def get_settings_service(db: AsyncSession = Depends(get_db)) -> SettingsService:
    return SettingsService(db)


async def get_credential_service(db: AsyncSession = Depends(get_db)) -> CredentialService:
    return CredentialService(db)


async def get_persona_service(db: AsyncSession = Depends(get_db)) -> PersonaService:
    return PersonaService(db)


async def get_ai_router(db: AsyncSession = Depends(get_db)) -> AIRouter:
    return AIRouter(db)


async def get_ai_usage_service(db: AsyncSession = Depends(get_db)) -> AIUsageService:
    return AIUsageService(db)


async def get_ai_routing_service(db: AsyncSession = Depends(get_db)) -> AIRoutingService:
    return AIRoutingService(db)


