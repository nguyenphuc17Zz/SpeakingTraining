import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask, ResponseFormat, ResponseFormatType
from app.domains.ai.router import AIRouter
from app.domains.learning.contracts import DifficultyLevel, ExerciseType, LearnerLearningState, PriorityScore, ScaffoldingLevel
from app.domains.learning.exercise_validator import ExerciseValidator
from app.domains.learning.exercise_variety_policy import ExerciseVarietyPolicy
from app.domains.learning.models import Exercise
from app.domains.learning.prompts import LearningPrompts
from app.domains.learning.templates.exercise_templates import get_template_for_type


class ExerciseGenerator:
    """Orchestrates AI-assisted and template-fallback generation of Japanese speaking exercises."""

    GENERATOR_VERSION = "1.0.0"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)

    async def generate_exercise(
        self,
        user_id: str,
        priority: PriorityScore,
        state: LearnerLearningState,
        recent_signatures: list[str] | None = None,
        recent_topics: list[str] | None = None,
    ) -> Exercise:
        """
        Generates a validated, personalized exercise targeting a specific priority weakness.
        Uses Templates + AI Personalization + Safety Validation + Fallback guarantee.
        """
        ex_type_str = priority.recommended_exercise_type.value
        item_type_str = priority.item_type.value
        template_info = get_template_for_type(ex_type_str, item_type_str)

        # 1. Attempt AI Personalization (pass reflex/keigo/pitch/situational overrides via extra_metadata if present)
        reflex_overrides = None
        keigo_overrides = None
        pitch_overrides = None
        situational_overrides = None
        if priority.recommended_exercise_type.value.startswith("reflex"):
            reflex_overrides = getattr(priority, "metadata", None) or {}
        if priority.recommended_exercise_type.value.startswith("keigo"):
            keigo_overrides = getattr(priority, "metadata", None) or {}
        if priority.recommended_exercise_type.value.startswith("pitch") or priority.recommended_exercise_type.value in ("mora_length", "vowel_devoicing", "pitch_contour", "pitch_recognition"):
            pitch_overrides = getattr(priority, "metadata", None) or {}
        if priority.recommended_exercise_type.value.startswith("situational"):
            situational_overrides = getattr(priority, "metadata", None) or {}
        ai_data = await self._generate_with_ai(user_id, priority, state, template_info, recent_topics, reflex_overrides, keigo_overrides, pitch_overrides, situational_overrides)

        # 2. Validate AI result
        is_valid = False
        if ai_data:
            is_valid, issues = ExerciseValidator.validate_exercise_data(ai_data)
            if not is_valid:
                logger.warning(f"[ExerciseGenerator] AI generated exercise failed validation: {issues}. Using fallback.")

        # 3. If AI failed or invalid, synthesize from Template fallback
        if not is_valid or not ai_data:
            ai_data = self._build_template_fallback(priority, template_info)

        # 4. Compute signature for anti-repetition
        sig = ExerciseVarietyPolicy.compute_exercise_signature(
            exercise_type=ex_type_str,
            target_patterns=ai_data.get("target_patterns", [priority.key]),
            difficulty=priority.difficulty.value,
            scenario_topic=ai_data.get("scenario"),
        )

        # 5. Determine scaffolding level
        scaffold_level_str = ScaffoldingLevel.NONE.value
        scaffold_hint = ai_data.get("scaffold_hint")
        if scaffold_hint and priority.difficulty == DifficultyLevel.EASY:
            scaffold_level_str = ScaffoldingLevel.KEYWORD_HINT.value

        # Preserve reflex/keigo/pitch/situational config if provided by template or AI
        extra_meta: dict[str, Any] = {"priority_score": priority.priority_score, "item_type": item_type_str}
        if ex_type_str.startswith("reflex"):
            _rc = {}
            if ai_data.get("reflex_config"):
                _rc.update(ai_data["reflex_config"])
            if reflex_overrides:
                _rc.update({k: v for k, v in reflex_overrides.items() if k in ("verb", "conjugation_target", "timer_limit_ms", "pressure_level", "prompt_mode", "subtitle_mode")})
            if ex_type_str == ExerciseType.REFLEX_CONJUGATION.value and not _rc.get("verb"):
                _rc.setdefault("verb", ai_data.get("verb") or priority.title.split()[0] if priority.title else "")
            if _rc:
                extra_meta["reflex_config"] = _rc
        if ex_type_str.startswith("keigo"):
            _kc = {}
            if ai_data.get("keigo_config"):
                _kc.update(ai_data["keigo_config"])
            if keigo_overrides:
                _kc.update({k: v for k, v in keigo_overrides.items() if k in ("timer_limit_ms", "pressure_level", "social_context", "target_register", "source_register")})
            if ai_data.get("timer_limit_ms"):
                _kc.setdefault("timer_limit_ms", ai_data["timer_limit_ms"])
            if _kc:
                extra_meta["keigo_config"] = _kc
        if ex_type_str.startswith("pitch") or ex_type_str in ("mora_length", "vowel_devoicing", "pitch_contour", "pitch_recognition"):
            _pc = {}
            if ai_data.get("pitch_config"):
                _pc.update(ai_data["pitch_config"])
            if pitch_overrides:
                _pc.update({k: v for k, v in pitch_overrides.items() if k in ("timer_limit_ms", "pressure_level", "pitch_pattern", "reading", "mora_count")})
            if ai_data.get("timer_limit_ms"):
                _pc.setdefault("timer_limit_ms", ai_data["timer_limit_ms"])
            if _pc:
                extra_meta["pitch_config"] = _pc
        if ex_type_str.startswith("situational"):
            _sc = {}
            if ai_data.get("situational_config"):
                _sc.update(ai_data["situational_config"])
            if situational_overrides:
                _sc.update({k: v for k, v in situational_overrides.items() if k in ("timer_limit_ms", "pressure_level", "location", "goals", "constraints", "seed", "mode", "duration_minutes")})
            if ai_data.get("timer_limit_ms"):
                _sc.setdefault("timer_limit_ms", ai_data["timer_limit_ms"])
            if _sc:
                extra_meta["situational_config"] = _sc

        exercise = Exercise(
            user_id=user_id,
            exercise_type=ex_type_str,
            status="not_started",
            title=ai_data["title"],
            objective=ai_data["objective"],
            scenario=ai_data.get("scenario"),
            instructions=ai_data["instructions"],
            constraints=ai_data.get("constraints", []),
            target_patterns=ai_data.get("target_patterns", [priority.key]),
            learning_item_keys=[priority.key],
            success_criteria=ai_data.get("success_criteria", ["Sử dụng đúng cấu trúc mục tiêu ít nhất 1 lần trong câu nói tự nhiên."]),
            acceptable_variants=ai_data.get("acceptable_variants", []),
            difficulty=priority.difficulty.value,
            scaffold_level=scaffold_level_str,
            scaffold_hint=scaffold_hint,
            estimated_minutes=ai_data.get("estimated_minutes", template_info["default_estimated_minutes"]),
            template_version=template_info.get("template_version", "v1"),
            generator_version=self.GENERATOR_VERSION,
            prompt_version=LearningPrompts.SITUATIONAL_GEN_PROMPT_VERSION if ex_type_str.startswith("situational") else LearningPrompts.PITCH_GEN_PROMPT_VERSION if ex_type_str.startswith("pitch") or ex_type_str in ("mora_length", "vowel_devoicing", "pitch_contour", "pitch_recognition") else LearningPrompts.KEIGO_GEN_PROMPT_VERSION if ex_type_str.startswith("keigo") else LearningPrompts.REFLEX_GEN_PROMPT_VERSION if ex_type_str.startswith("reflex") else LearningPrompts.GEN_PROMPT_VERSION,
            provider=ai_data.get("_provider"),
            model=ai_data.get("_model"),
            exercise_signature=sig,
            extra_metadata=extra_meta,
        )

        self.db.add(exercise)
        await self.db.flush()
        logger.info(f"[ExerciseGenerator] Created exercise '{exercise.title}' (ID: {exercise.id}) for user '{user_id}'")
        return exercise

    async def _generate_with_ai(
        self,
        user_id: str,
        priority: PriorityScore,
        state: LearnerLearningState,
        template_info: dict[str, Any],
        recent_topics: list[str] | None,
        reflex_overrides: dict[str, Any] | None = None,
        keigo_overrides: dict[str, Any] | None = None,
        pitch_overrides: dict[str, Any] | None = None,
        situational_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Calls AIRouter to personalize template into structured exercise JSON."""
        # Check if reflex/keigo/pitch/situational exercise (needs specialized prompt)
        is_reflex = priority.recommended_exercise_type.value.startswith("reflex")
        is_keigo = priority.recommended_exercise_type.value.startswith("keigo")
        is_pitch = priority.recommended_exercise_type.value.startswith("pitch") or priority.recommended_exercise_type.value in ("mora_length", "vowel_devoicing", "pitch_contour", "pitch_recognition")
        is_situational = priority.recommended_exercise_type.value.startswith("situational")
        if is_reflex:
            pressure = (reflex_overrides or {}).get("pressure_level", "normal")
            timer_ms = (reflex_overrides or {}).get("timer_limit_ms", 4000)
            verb = (reflex_overrides or {}).get("verb")
            target = (reflex_overrides or {}).get("conjugation_target")
            sys_inst, user_content = LearningPrompts.build_reflex_generation_prompt(
                sub_mode=priority.recommended_exercise_type.value,
                priority=priority,
                state=state,
                template_info=template_info,
                pressure_level=pressure,
                timer_ms=timer_ms,
                verb=verb,
                conjugation_target=target,
            )
            task = AITask.REFLEX_GENERATION
            max_tokens = 700
        elif is_keigo:
            pressure = (keigo_overrides or {}).get("pressure_level", "normal")
            timer_ms = (keigo_overrides or {}).get("timer_limit_ms", 5000)
            ctx = (keigo_overrides or {}).get("social_context")
            sys_inst, user_content = LearningPrompts.build_keigo_generation_prompt(
                sub_mode=priority.recommended_exercise_type.value,
                priority=priority,
                state=state,
                template_info=template_info,
                pressure_level=pressure,
                timer_ms=timer_ms,
                social_context=ctx,
            )
            task = AITask.KEIGO_GENERATION
            max_tokens = 700
        elif is_pitch:
            pressure = (pitch_overrides or {}).get("pressure_level", "normal")
            timer_ms = (pitch_overrides or {}).get("timer_limit_ms", 5000)
            pattern = (pitch_overrides or {}).get("pitch_pattern")
            sys_inst, user_content = LearningPrompts.build_pitch_generation_prompt(
                sub_mode=priority.recommended_exercise_type.value,
                priority=priority,
                state=state,
                template_info=template_info,
                pressure_level=pressure,
                timer_ms=timer_ms,
                pitch_pattern=pattern,
            )
            task = AITask.PITCH_GENERATION if hasattr(AITask, "PITCH_GENERATION") else AITask.EXERCISE_GENERATION
            max_tokens = 700
        elif is_situational:
            pressure = (situational_overrides or {}).get("pressure_level", "normal")
            timer_ms = (situational_overrides or {}).get("timer_limit_ms", 6000)
            ctx = (situational_overrides or {}).get("situational_context") or situational_overrides
            sys_inst, user_content = LearningPrompts.build_situational_generation_prompt(
                sub_mode=priority.recommended_exercise_type.value,
                priority=priority,
                state=state,
                template_info=template_info,
                pressure_level=pressure,
                timer_ms=timer_ms,
                situational_context=ctx,
            )
            task = AITask.SITUATIONAL_GENERATION if hasattr(AITask, "SITUATIONAL_GENERATION") else AITask.EXERCISE_GENERATION
            max_tokens = 700
        else:
            sys_inst, user_content = LearningPrompts.build_exercise_generation_prompt(
                priority=priority,
                state=state,
                template_info=template_info,
                recent_topics=recent_topics,
            )
            task = AITask.EXERCISE_GENERATION
            max_tokens = 600

        req = AIRequest(
            task=task,
            system_instruction=sys_inst,
            messages=[
                AIMessage(role=AIMessageRole.SYSTEM, content=sys_inst),
                AIMessage(role=AIMessageRole.USER, content=user_content),
            ],
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.5,
            max_output_tokens=max_tokens,
            user_id=user_id,
        )

        try:
            resp = await self.ai_router.generate(task=task, request=req, user_id=user_id)
            clean_text = resp.text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text.replace("```json", "", 1).rstrip("```").strip()
            elif clean_text.startswith("```"):
                clean_text = clean_text.replace("```", "", 1).rstrip("```").strip()

            parsed = json.loads(clean_text)
            parsed["_provider"] = resp.provider
            parsed["_model"] = resp.model
            return parsed
        except Exception as e:
            logger.warning(f"[ExerciseGenerator] AI generation error: {e}")
            return None

    def _build_template_fallback(
        self,
        priority: PriorityScore,
        template_info: dict[str, Any],
    ) -> dict[str, Any]:
        """Creates robust deterministic fallback exercise when AI is unavailable."""
        target_name = priority.title
        key_raw = priority.key.split(".")[-1]

        title = template_info["title_template"].format(target_title=target_name)
        obj = template_info["objective_template"].format(target_title=target_name)
        scenario = template_info.get("scenario_template", "Giao tiếp công sở và đời sống hàng ngày.")
        inst = template_info["instruction_template"].format(target_title=target_name)

        return {
            "title": title,
            "objective": obj,
            "scenario": scenario,
            "instructions": inst,
            "constraints": ["Trả lời tự nhiên bằng tiếng Nhật, giữ nhịp nói đều đặn."],
            "target_patterns": [key_raw, target_name],
            "acceptable_variants": [target_name],
            "scaffold_hint": f"Hãy nghĩ đến ngữ cảnh dùng: {target_name}",
            "estimated_minutes": template_info.get("default_estimated_minutes", 5),
            "_provider": "template_fallback",
            "_model": "deterministic_v1",
        }
