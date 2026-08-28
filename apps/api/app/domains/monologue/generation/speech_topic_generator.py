"""SpeechTopicGenerator — dynamic AI + deterministic fallback, no hard-coded topic DB."""

from __future__ import annotations

import hashlib
import json
import random
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask, ResponseFormat, ResponseFormatType
from app.domains.ai.router import AIRouter
from app.domains.monologue.contracts import (
    SpeechGenre,
    SpeechSupport,
    SpeechSupportLevel,
    SpeechTaskSpec,
    SpeechTopicDomain,
)
from app.domains.monologue.generation.constraint_generator import ConstraintGenerator
from app.domains.monologue.generation.difficulty_generator import DifficultyGenerator, PreparationHintGenerator
from app.domains.monologue.generation.genre_generator import SpeechGenreGenerator
from app.domains.monologue.generation.genre_ontology import ALL_DOMAINS
from app.domains.monologue.generation.topic_validator import TopicValidator
from app.domains.monologue.generation.variety_policy import SpeechVarietyPolicy


class SpeechTopicGenerator:
    GENERATOR_VERSION = "monologue.gen.v1"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)
        self.genre_gen = SpeechGenreGenerator()
        self.constraint_gen = ConstraintGenerator()
        self.diff_gen = DifficultyGenerator()

    async def generate(
        self,
        inp: Any,  # SpeechGenerationInput dict or model
        max_retries: int = 2,
    ) -> SpeechTaskSpec:
        # normalize input
        if isinstance(inp, dict):
            data = inp
        else:
            data = inp.model_dump() if hasattr(inp, "model_dump") else dict(inp)

        user_id: str = data.get("user_id") or "default"
        level: str = (data.get("overall_level") or data.get("level") or "N3").upper()
        speaking_level = data.get("speaking_level") or level
        duration_sec: int = int(data.get("duration_sec") or 60)
        prep_sec_raw = data.get("prep_sec")
        difficulty_raw = data.get("difficulty")
        genre_raw: str | None = data.get("genre")
        support_level_raw = data.get("support_level")
        topic_domain_raw: str | None = data.get("topic_domain")
        seed: str | None = data.get("seed")
        interests: list[str] = data.get("interests") or []
        career_domain: str | None = data.get("career_domain")
        recent_sigs: list[str] = data.get("recent_signatures") or []
        recent_topics: list[str] = data.get("recent_topics") or []
        recent_genres: list[str] = data.get("recent_genres") or []
        weaknesses: list[dict[str, Any]] = data.get("weaknesses") or data.get("learning_targets") or []

        # 1. Genre selection (if not forced)
        if genre_raw and genre_raw.lower() in [g.value for g in SpeechGenre]:
            genre = SpeechGenre(genre_raw.lower())
        else:
            # derive career goals from career_domain + active_goals
            career_goals = []
            if career_domain:
                career_goals.append(career_domain)
            active_goals = data.get("active_goals") or []
            career_goals.extend(active_goals)
            genre = self.genre_gen.select(
                learner_level=level,
                recent_genres=recent_genres,
                weaknesses=weaknesses,
                career_goals=career_goals,
                duration_sec=duration_sec,
                seed=seed,
            )

        # 2. Difficulty & prep & support
        difficulty = int(difficulty_raw) if difficulty_raw else self.diff_gen.difficulty_for(level, genre, duration_sec)
        prep_sec = int(prep_sec_raw) if prep_sec_raw is not None else self.diff_gen.prep_sec_for(difficulty, duration_sec, level)
        if support_level_raw is not None:
            try:
                support_level = SpeechSupportLevel(int(support_level_raw))
            except Exception:
                support_level = self.diff_gen.support_level_for(difficulty, level, genre)
        else:
            support_level = self.diff_gen.support_level_for(difficulty, level, genre)

        # 3. Domain + constraints
        if topic_domain_raw and topic_domain_raw.lower() in [d.value for d in SpeechTopicDomain]:
            domain = SpeechTopicDomain(topic_domain_raw.lower())
        else:
            # pick domain correlated to genre/interests
            rng = random.Random(seed) if seed else random
            # bias toward interests
            domain = rng.choice(ALL_DOMAINS)
            # simple interest→domain mapping
            interest_map = {
                "technology": SpeechTopicDomain.TECHNOLOGY,
                "tech": SpeechTopicDomain.TECHNOLOGY,
                "games": SpeechTopicDomain.CULTURE,
                "fitness": SpeechTopicDomain.HEALTH,
                "travel": SpeechTopicDomain.TRAVEL,
                "food": SpeechTopicDomain.FOOD,
                "programming": SpeechTopicDomain.TECHNOLOGY,
                "business": SpeechTopicDomain.BUSINESS,
                "career": SpeechTopicDomain.CAREER,
            }
            for it in interests:
                if it.lower() in interest_map:
                    domain = interest_map[it.lower()]
                    break

        constraints = self.constraint_gen.generate(genre, difficulty, duration_sec, seed=seed)

        # 4. Generate via AI — no mock fallback (hard error per user choice)
        ai_spec = await self._generate_with_ai(
            user_id=user_id,
            level=level,
            speaking_level=speaking_level,
            genre=genre,
            domain=domain,
            difficulty=difficulty,
            duration_sec=duration_sec,
            prep_sec=prep_sec,
            support_level=support_level,
            constraints=constraints,
            interests=interests,
            career_domain=career_domain,
            weaknesses=weaknesses,
            recent_topics=recent_topics,
            seed=seed,
        )
        if ai_spec is None:
            raise RuntimeError("AI topic generation failed — no fallback (configure AI provider or retry)")

        # 5. Validate; retry via AI only (no template fallback)
        attempts = 0
        spec = ai_spec
        while attempts <= max_retries:
            # compute signature
            sig = SpeechVarietyPolicy.compute_signature(
                normalized_topic=spec.topic,
                genre=spec.genre.value if isinstance(spec.genre, SpeechGenre) else str(spec.genre),
                topic_domain=spec.topic_domain.value if isinstance(spec.topic_domain, SpeechTopicDomain) else str(spec.topic_domain),
                difficulty=spec.difficulty,
                duration_sec=spec.expected_duration_sec,
                constraint_sig=",".join(sorted(spec.constraints)),
            )
            spec.session_signature = sig
            valid, issues = TopicValidator.validate(
                topic=spec.topic,
                instruction=spec.instruction,
                genre=spec.genre,
                difficulty=spec.difficulty,
                duration_sec=spec.expected_duration_sec,
                topic_domain=spec.topic_domain.value if isinstance(spec.topic_domain, SpeechTopicDomain) else str(spec.topic_domain),
                constraints=spec.constraints,
                support_level=spec.support_level,
                session_signature=sig,
                recent_signatures=recent_sigs,
            )
            near_dup = SpeechVarietyPolicy.is_near_duplicate_topic(spec.topic, recent_topics)
            if valid and not near_dup:
                # fill support deterministically if AI omitted (structured, not sliced topic)
                if not spec.support.keywords and not spec.support.outline and not spec.support.guided_questions:
                    if spec.support_level == SpeechSupportLevel.GUIDED_QUESTIONS:
                        spec.support.guided_questions = PreparationHintGenerator.guided_questions(genre)
                    elif spec.support_level == SpeechSupportLevel.STRUCTURE:
                        spec.support.outline = PreparationHintGenerator.structure_outline(genre)
                    # BLIND/KEYWORDS/MINIMAL stay as AI provided or empty
                return spec
            logger.warning(f"[SpeechTopicGenerator] validation failed: {issues} near_dup={near_dup} retry {attempts}")
            if attempts >= max_retries:
                raise RuntimeError(f"Generated topic failed validation after {max_retries+1} attempts: {issues} / near_dup={near_dup}")
            # regenerate via AI with perturbed seed
            ai_spec = await self._generate_with_ai(
                user_id=user_id, level=level, speaking_level=speaking_level, genre=genre,
                domain=domain, difficulty=difficulty, duration_sec=duration_sec, prep_sec=prep_sec,
                support_level=support_level, constraints=constraints, interests=interests,
                career_domain=career_domain, weaknesses=weaknesses, recent_topics=recent_topics + [spec.topic], seed=(seed or "") + str(attempts)
            )
            if ai_spec is None:
                raise RuntimeError("AI regeneration failed — no fallback")
            spec = ai_spec
            attempts += 1

        raise RuntimeError("Unreachable: topic generation exhausted")

    async def _generate_with_ai(
        self,
        user_id: str,
        level: str,
        speaking_level: str,
        genre: SpeechGenre,
        domain: SpeechTopicDomain,
        difficulty: int,
        duration_sec: int,
        prep_sec: int,
        support_level: SpeechSupportLevel,
        constraints: list[str],
        interests: list[str],
        career_domain: str | None,
        weaknesses: list[dict[str, Any]],
        recent_topics: list[str],
        seed: str | None,
    ) -> SpeechTaskSpec | None:
        from app.domains.monologue.ai.prompts import MonologuePrompts

        sys_inst, user_content = MonologuePrompts.build_generation_prompt(
            level=level,
            speaking_level=speaking_level,
            genre=genre,
            domain=domain,
            difficulty=difficulty,
            duration_sec=duration_sec,
            prep_sec=prep_sec,
            support_level=support_level,
            constraints=constraints,
            interests=interests,
            career_domain=career_domain,
            weaknesses=weaknesses,
            recent_topics=recent_topics,
            seed=seed,
        )
        # choose AITask — fall back to EXERCISE_GENERATION if new task not yet in registry
        from app.domains.ai.contracts import AITask

        task = getattr(AITask, "SPEECH_GENERATION", AITask.EXERCISE_GENERATION)
        req = AIRequest(
            task=task,
            system_instruction=sys_inst,
            messages=[
                AIMessage(role=AIMessageRole.SYSTEM, content=sys_inst),
                AIMessage(role=AIMessageRole.USER, content=user_content),
            ],
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.6,
            max_output_tokens=900,
            user_id=user_id,
            metadata={"seed": seed or ""},
        )
        try:
            resp = await self.ai_router.generate(task=task, request=req, user_id=user_id)
            txt = resp.text.strip()
            if txt.startswith("```json"):
                txt = txt.replace("```json", "", 1).rstrip("```").strip()
            elif txt.startswith("```"):
                txt = txt.replace("```", "", 1).rstrip("```").strip()
            parsed = json.loads(txt)
            # Map to SpeechTaskSpec (VI topic + JP instruction hybrid §47 answer)
            topic = parsed.get("topic") or parsed.get("title") or ""
            instruction = parsed.get("instruction") or parsed.get("speech_task") or ""
            # ensure JP instruction (if AI gave VI, keep but map)
            jp_instr = parsed.get("instruction_ja") or instruction
            # fallback: if instruction lacks Japanese, keep as is (hybrid allowed)
            support = SpeechSupport(
                keywords=parsed.get("keywords") or [],
                outline=parsed.get("outline") or parsed.get("outline_hint") or [],
                guided_questions=parsed.get("guided_questions") or [],
            )
            spec = SpeechTaskSpec(
                topic=str(topic).strip(),
                instruction=str(jp_instr).strip(),
                genre=genre,
                topic_domain=domain,
                difficulty=int(parsed.get("difficulty") or difficulty),
                expected_duration_sec=int(parsed.get("expected_duration_sec") or parsed.get("duration_sec") or duration_sec),
                prep_duration_sec=int(parsed.get("prep_duration_sec") or parsed.get("prep_sec") or prep_sec),
                support_level=support_level,
                support=support,
                constraints=parsed.get("constraints") or constraints,
                learning_targets=parsed.get("learning_targets") or [],
                outline_hint=parsed.get("outline_hint") or parsed.get("outline") or [],
                provider=resp.provider,
                model=resp.model,
            )
            if not spec.topic or not spec.instruction:
                logger.warning(f"[SpeechTopicGenerator] AI returned empty topic/instruction: {parsed}")
                return None
            return spec
        except Exception as e:
            logger.warning(f"[SpeechTopicGenerator] AI generation failed: {e}", exc_info=True)
            return None
