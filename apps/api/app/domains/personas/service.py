from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import json

from app.domains.personas.models import Persona
from app.domains.personas.schemas import PersonaCreate, PersonaGenerateRequest, PersonaGenerateResponse, PersonaUpdate
from app.domains.personas.seeds import SYSTEM_PERSONAS_SEED
from app.shared.errors.exceptions import NotFoundException, ValidationException


class PersonaService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def seed_system_personas(self) -> None:
        """Seeds standard built-in personas into the database only if the table is completely empty."""
        result = await self.session.execute(select(Persona))
        has_any = result.scalars().first() is not None
        if not has_any:
            for p_data in SYSTEM_PERSONAS_SEED:
                persona = Persona(
                    id=p_data["id"],
                    name=p_data["name"],
                    description=p_data["description"],
                    role=p_data["role"],
                    personality=p_data["personality"],
                    speaking_style=p_data["speaking_style"],
                    difficulty=p_data["difficulty"],
                    is_system=True,
                    avatar_url=p_data.get("avatar_url"),
                    system_prompt=p_data.get("system_prompt"),
                )
                self.session.add(persona)
            await self.session.commit()

    async def restore_default_personas(self) -> list[Persona]:
        """Restores missing standard built-in personas into the database on user request."""
        for p_data in SYSTEM_PERSONAS_SEED:
            result = await self.session.execute(
                select(Persona).where(Persona.id == p_data["id"])
            )
            existing = result.scalar_one_or_none()
            if not existing:
                persona = Persona(
                    id=p_data["id"],
                    name=p_data["name"],
                    description=p_data["description"],
                    role=p_data["role"],
                    personality=p_data["personality"],
                    speaking_style=p_data["speaking_style"],
                    difficulty=p_data["difficulty"],
                    is_system=True,
                    avatar_url=p_data.get("avatar_url"),
                    system_prompt=p_data.get("system_prompt"),
                )
                self.session.add(persona)
        await self.session.commit()
        return await self.list_personas()

    async def list_personas(self) -> list[Persona]:
        result = await self.session.execute(
            select(Persona).order_by(Persona.is_system.desc(), Persona.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, persona_id: str) -> Persona:
        result = await self.session.execute(
            select(Persona).where(Persona.id == persona_id)
        )
        persona = result.scalar_one_or_none()
        if not persona:
            raise NotFoundException(f"Persona with ID '{persona_id}' not found")
        return persona

    async def create_persona(self, payload: PersonaCreate) -> Persona:
        if not payload.name.strip():
            raise ValidationException("Persona name cannot be empty")

        persona = Persona(
            name=payload.name.strip(),
            description=payload.description.strip(),
            role=payload.role.strip(),
            personality=payload.personality.strip(),
            speaking_style=payload.speaking_style.strip(),
            difficulty=payload.difficulty.strip().upper(),
            is_system=False,
            avatar_url=payload.avatar_url,
            system_prompt=payload.system_prompt,
        )
        self.session.add(persona)
        await self.session.commit()
        await self.session.refresh(persona)
        return persona

    async def update_persona(self, persona_id: str, payload: PersonaUpdate) -> Persona:
        persona = await self.get_by_id(persona_id)

        update_data = payload.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            setattr(persona, key, val)

        await self.session.commit()
        await self.session.refresh(persona)
        return persona

    async def delete_persona(self, persona_id: str) -> None:
        persona = await self.get_by_id(persona_id)
        await self.session.delete(persona)
        await self.session.commit()

    # --- AI random generation ---

    async def generate_random_persona(
        self, req: PersonaGenerateRequest, user_id: str | None = None
    ) -> PersonaGenerateResponse:
        # Lazy import to avoid circular dependencies
        from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask
        from app.domains.ai.router import AIRouter

        difficulty = (req.difficulty or "N3").upper().strip()
        if difficulty not in ["N5", "N4", "N3", "N2", "N1"]:
            difficulty = "N3"

        theme_hint = (req.theme or "").strip()

        system = (
            "You are an expert Japanese conversation persona designer for language learners. "
            "Generate ONE Japanese conversation partner (persona) formatted strictly as a JSON object with keys: "
            "name (Japanese name with kanji/kana and romaji, e.g., 'Haruto (ハルト)'), "
            "role (Role or occupation in Vietnamese, e.g., 'Chủ quán ramen tại Tokyo'), "
            "description (1-2 sentences in Vietnamese describing context and background), "
            "personality (Vietnamese description of personality traits), "
            "speaking_style (Vietnamese description of speech style, mentioning politeness/keigo/casual), "
            "difficulty (One of 'N5', 'N4', 'N3', 'N2', 'N1'), "
            "system_prompt (System prompt in English instructing the AI how to roleplay this persona naturally, keeping responses concise 1-3 sentences suitable for learner JLPT level). "
            "Return ONLY raw valid JSON, no markdown formatting."
        )

        user_content = f"Generate a unique conversation partner. Target JLPT Level: {difficulty}."
        if theme_hint:
            user_content += f" Specific theme/scenario: {theme_hint}."

        try:
            ai_router = AIRouter(self.session)
            ai_req = AIRequest(
                messages=[AIMessage(role=AIMessageRole.USER, content=user_content)],
                system_instruction=system,
                temperature=0.85,
                max_output_tokens=600,
                response_format=None,
            )
            resp = await ai_router.generate(task=AITask.GENERAL, request=ai_req, user_id=user_id)
            text = resp.text.strip()

            # Extract JSON
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1:
                raise ValidationException("AI response could not be parsed as JSON.")

            obj = json.loads(text[start : end + 1])
            for k in ["name", "role", "description", "personality", "speaking_style"]:
                if k not in obj or not str(obj[k]).strip():
                    raise ValidationException(f"AI generated incomplete persona: missing '{k}'")

            diff = str(obj.get("difficulty", difficulty)).upper().strip()
            if diff not in ["N5", "N4", "N3", "N2", "N1"]:
                diff = difficulty

            return PersonaGenerateResponse(
                name=str(obj["name"]).strip()[:100],
                role=str(obj["role"]).strip()[:100],
                description=str(obj["description"]).strip(),
                personality=str(obj["personality"]).strip(),
                speaking_style=str(obj["speaking_style"]).strip()[:100],
                difficulty=diff,
                avatar_url=None,
                system_prompt=str(obj.get("system_prompt", "")).strip() or f"You are {obj['name']}, {obj['role']}. Respond naturally in Japanese in 1-3 sentences.",
                reasoning=f"AI ({resp.provider}/{resp.model})",
            )
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Không thể tạo persona ngẫu nhiên bằng AI: {e}")
