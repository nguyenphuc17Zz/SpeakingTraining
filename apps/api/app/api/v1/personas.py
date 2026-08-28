
from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user, get_persona_service
from app.domains.personas.schemas import PersonaCreate, PersonaGenerateRequest, PersonaGenerateResponse, PersonaRead, PersonaUpdate
from app.domains.personas.service import PersonaService
from app.domains.users.models import User

router = APIRouter(prefix="/personas", tags=["Personas"])


@router.post("/generate", response_model=PersonaGenerateResponse, summary="Generate Random Persona via AI")
async def generate_persona(
    payload: PersonaGenerateRequest,
    current_user: User = Depends(get_current_user),
    service: PersonaService = Depends(get_persona_service),
):
    return await service.generate_random_persona(payload, user_id=current_user.id)


@router.post("/restore-defaults", response_model=list[PersonaRead], summary="Restore Default System Personas")
async def restore_defaults(service: PersonaService = Depends(get_persona_service)):
    return await service.restore_default_personas()


@router.get("", response_model=list[PersonaRead], summary="List All Personas")
async def list_personas(service: PersonaService = Depends(get_persona_service)):
    return await service.list_personas()


@router.get("/{persona_id}", response_model=PersonaRead, summary="Get Persona by ID")
async def get_persona(persona_id: str, service: PersonaService = Depends(get_persona_service)):
    return await service.get_by_id(persona_id=persona_id)


@router.post(
    "",
    response_model=PersonaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Custom Persona",
)
async def create_persona(
    payload: PersonaCreate,
    service: PersonaService = Depends(get_persona_service),
):
    return await service.create_persona(payload=payload)


@router.patch("/{persona_id}", response_model=PersonaRead, summary="Update Persona")
async def update_persona(
    persona_id: str,
    payload: PersonaUpdate,
    service: PersonaService = Depends(get_persona_service),
):
    return await service.update_persona(persona_id=persona_id, payload=payload)


@router.delete(
    "/{persona_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Custom Persona",
)
async def delete_persona(
    persona_id: str,
    service: PersonaService = Depends(get_persona_service),
):
    await service.delete_persona(persona_id=persona_id)
