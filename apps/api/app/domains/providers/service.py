
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_encryption_service, mask_secret
from app.domains.providers.models import APICredential
from app.domains.providers.registry import (
    get_all_providers_metadata,
    get_provider_metadata,
)
from app.domains.providers.schemas import (
    CredentialCreate,
    CredentialRead,
    CredentialUpdate,
    ProviderDetailRead,
)
from app.shared.errors.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)


class CredentialService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.encryption = get_encryption_service()
        from app.domains.users.service import UserService
        self.user_service = UserService(session)

    async def list_providers_with_status(self, user_id: str | None = None) -> list[ProviderDetailRead]:
        if not user_id:
            user = await self.user_service.get_or_create_default_user()
            user_id = user.id

        result = await self.session.execute(
            select(APICredential).where(APICredential.user_id == user_id)
        )
        credentials = result.scalars().all()
        cred_map = {c.provider.lower(): c for c in credentials}

        providers_meta = get_all_providers_metadata()
        output: list[ProviderDetailRead] = []

        from app.domains.ai.discovery import model_discovery_service

        for p_meta in providers_meta:
            cred = cred_map.get(p_meta.id.lower())
            cred_read: CredentialRead | None = None
            is_configured = False
            raw_secret: str | None = None

            if cred:
                try:
                    raw_secret = self.encryption.decrypt(cred.encrypted_secret)
                    masked = mask_secret(raw_secret)
                except Exception:
                    masked = "••••••••[Corrupted]"
                is_configured = True
                cred_read = CredentialRead(
                    id=cred.id,
                    user_id=cred.user_id,
                    provider=cred.provider,
                    masked_secret=masked,
                    is_enabled=cred.is_enabled,
                    is_configured=True,
                    created_at=cred.created_at,
                    updated_at=cred.updated_at,
                )

            # Dynamically fetch models if configured, else fallback
            dynamic_models = await model_discovery_service.get_models_for_provider(
                provider_id=p_meta.id,
                api_key=raw_secret if is_configured else None,
            )
            resolved_models = dynamic_models if dynamic_models else p_meta.models

            output.append(
                ProviderDetailRead(
                    id=p_meta.id,
                    display_name=p_meta.display_name,
                    description=p_meta.description,
                    default_model=p_meta.default_model,
                    models=resolved_models,
                    is_configured=is_configured,
                    requires_api_key=p_meta.requires_api_key,
                    documentation_url=p_meta.documentation_url,
                    credential=cred_read,
                )
            )

        return output

    async def create_credential(self, payload: CredentialCreate, user_id: str | None = None) -> CredentialRead:
        if not user_id:
            user = await self.user_service.get_or_create_default_user()
            user_id = user.id

        provider_id = payload.provider.lower().strip()
        if not get_provider_metadata(provider_id):
            raise ValidationException(f"Unsupported provider: '{payload.provider}'")

        if not payload.api_key.strip():
            raise ValidationException("API key cannot be empty")

        # Check existing
        result = await self.session.execute(
            select(APICredential).where(
                APICredential.user_id == user_id,
                APICredential.provider == provider_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ConflictException(f"Credential for provider '{provider_id}' already exists. Use PATCH to update.")

        encrypted_key = self.encryption.encrypt(payload.api_key.strip())
        cred = APICredential(
            user_id=user_id,
            provider=provider_id,
            encrypted_secret=encrypted_key,
            is_enabled=payload.is_enabled,
        )
        self.session.add(cred)
        await self.session.commit()
        await self.session.refresh(cred)

        from app.domains.ai.discovery import model_discovery_service
        model_discovery_service.clear_cache(provider_id)

        return CredentialRead(
            id=cred.id,
            user_id=cred.user_id,
            provider=cred.provider,
            masked_secret=mask_secret(payload.api_key.strip()),
            is_enabled=cred.is_enabled,
            is_configured=True,
            created_at=cred.created_at,
            updated_at=cred.updated_at,
        )

    async def update_credential(self, credential_id: str, payload: CredentialUpdate) -> CredentialRead:
        result = await self.session.execute(
            select(APICredential).where(APICredential.id == credential_id)
        )
        cred = result.scalar_one_or_none()
        if not cred:
            raise NotFoundException(f"Credential with ID '{credential_id}' not found")

        if payload.api_key is not None:
            if not payload.api_key.strip():
                raise ValidationException("API key cannot be empty")
            cred.encrypted_secret = self.encryption.encrypt(payload.api_key.strip())

        if payload.is_enabled is not None:
            cred.is_enabled = payload.is_enabled

        await self.session.commit()
        await self.session.refresh(cred)

        from app.domains.ai.discovery import model_discovery_service
        model_discovery_service.clear_cache(cred.provider)

        try:
            raw_secret = self.encryption.decrypt(cred.encrypted_secret)
            masked = mask_secret(raw_secret)
        except Exception:
            masked = "••••••••"

        return CredentialRead(
            id=cred.id,
            user_id=cred.user_id,
            provider=cred.provider,
            masked_secret=masked,
            is_enabled=cred.is_enabled,
            is_configured=True,
            created_at=cred.created_at,
            updated_at=cred.updated_at,
        )

    async def delete_credential(self, credential_id: str) -> None:
        result = await self.session.execute(
            select(APICredential).where(APICredential.id == credential_id)
        )
        cred = result.scalar_one_or_none()
        if not cred:
            raise NotFoundException(f"Credential with ID '{credential_id}' not found")

        provider_to_clear = cred.provider
        await self.session.delete(cred)
        await self.session.commit()

        from app.domains.ai.discovery import model_discovery_service
        model_discovery_service.clear_cache(provider_to_clear)

    async def get_raw_key_for_provider(self, provider_id: str, user_id: str | None = None) -> str | None:
        """Internal method for Phase 2 AI engine to retrieve decrypted key in-memory."""
        if not user_id:
            user = await self.user_service.get_or_create_default_user()
            user_id = user.id

        result = await self.session.execute(
            select(APICredential).where(
                APICredential.user_id == user_id,
                APICredential.provider == provider_id.lower().strip(),
                APICredential.is_enabled.is_(True),
            )
        )
        cred = result.scalar_one_or_none()
        if not cred:
            return None
        return self.encryption.decrypt(cred.encrypted_secret)
