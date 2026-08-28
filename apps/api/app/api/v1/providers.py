
from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_credential_service, get_current_user
from app.domains.providers.schemas import (
    CredentialCreate,
    CredentialRead,
    CredentialUpdate,
    ProviderDetailRead,
)
from app.domains.providers.service import CredentialService
from app.domains.users.models import User

router = APIRouter(prefix="/providers", tags=["Providers & Credentials"])


@router.get("", response_model=list[ProviderDetailRead], summary="List AI Providers & Config Status")
async def list_providers(
    current_user: User = Depends(get_current_user),
    service: CredentialService = Depends(get_credential_service),
):
    return await service.list_providers_with_status(user_id=current_user.id)


@router.post(
    "/credentials",
    response_model=CredentialRead,
    status_code=status.HTTP_201_CREATED,
    summary="Save Encrypted Provider API Key",
)
async def create_credential(
    payload: CredentialCreate,
    current_user: User = Depends(get_current_user),
    service: CredentialService = Depends(get_credential_service),
):
    return await service.create_credential(payload=payload, user_id=current_user.id)


@router.patch(
    "/credentials/{credential_id}",
    response_model=CredentialRead,
    summary="Update Provider Credential",
)
async def update_credential(
    credential_id: str,
    payload: CredentialUpdate,
    service: CredentialService = Depends(get_credential_service),
):
    return await service.update_credential(credential_id=credential_id, payload=payload)


@router.delete(
    "/credentials/{credential_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Provider Credential",
)
async def delete_credential(
    credential_id: str,
    service: CredentialService = Depends(get_credential_service),
):
    await service.delete_credential(credential_id=credential_id)
