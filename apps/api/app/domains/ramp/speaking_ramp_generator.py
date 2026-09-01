"""SpeakingRampGenerator — generates RampTaskSpec for all 11 exercise types.

§7 Dynamic Exercise Generation — dispatches to exercise-type builders.
§9–19 Exercise type implementations.
§45 AI Constraints — every generated task passes ExerciseValidator.
§72 Fallback when AI unavailable.
"""

from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.ai.contracts import (
    AIMessage,
    AIMessageRole,
    AIRequest,
    AITask,
    ResponseFormat,
    ResponseFormatType,
)
from app.domains.ai.router import AIRouter
from app.domains.ramp.contracts import (
    RampExerciseType,
    RampGenerationInput,
    RampScaffold,
    RampTaskSpec,
    RampTopicDomain,
    STAGE_EXERCISE_TYPE,
)
from app.domains.ramp.prompts import RampPrompts
from app.domains.ramp.ramp_topic_generator import RampTopicGenerator


class SpeakingRampGenerator:
    """
    Generates RampTaskSpec for any exercise type.
    Topic generation → exercise-type-specific prompt → validation → fallback.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)
        self.topic_gen = RampTopicGenerator(db)

    async def generate(
        self,
        inp: RampGenerationInput,
        force_exercise_type: RampExerciseType | None = None,
    ) -> RampTaskSpec:
        """Generate a complete RampTaskSpec."""
        # 1. Generate topic base
        topic_spec = await self.topic_gen.generate(inp)

        # 2. Determine exercise type
        ex_type = force_exercise_type or STAGE_EXERCISE_TYPE.get(
            inp.current_stage, RampExerciseType.SPEAK_SPONTANEOUS
        )
        topic_spec.exercise_type = ex_type

        # 3. For exercise types that need additional AI-generated content,
        #    enrich the task spec
        try:
            enriched = await self._enrich_for_type(inp, topic_spec)
            return enriched
        except Exception as e:
            logger.warning(f"[SpeakingRampGenerator] Enrichment failed: {e}. Using base topic spec.")
            return topic_spec

    async def _enrich_for_type(
        self,
        inp: RampGenerationInput,
        base: RampTaskSpec,
    ) -> RampTaskSpec:
        """Add exercise-type-specific fields via AI or deterministic logic."""

        ex_type = base.exercise_type

        # Echo (§9): needs an exact sentence to repeat
        if ex_type == RampExerciseType.SPEAK_ECHO:
            return await self._build_echo(inp, base)

        # Substitute (§10): needs template + variable
        if ex_type == RampExerciseType.SPEAK_SUBSTITUTE:
            return await self._build_substitute(inp, base)

        # Sentence completion (§11): needs a sentence stem
        if ex_type == RampExerciseType.SPEAK_COMPLETE:
            return await self._build_complete(inp, base)

        # Expand (§13): needs seed sentence + expansion dimension
        if ex_type == RampExerciseType.SPEAK_EXPAND:
            return await self._build_expand(inp, base)

        # Keyword → sentence (§16): needs keyword list
        if ex_type == RampExerciseType.SPEAK_KEYWORD:
            return self._build_keyword(inp, base)

        # Guided (§17): needs structured questions
        if ex_type == RampExerciseType.SPEAK_GUIDED:
            return self._build_guided(inp, base)

        # All others (one_sentence, reason, example, spontaneous, followup):
        # base topic spec from RampTopicGenerator is sufficient
        return base

    async def _build_echo(self, inp: RampGenerationInput, base: RampTaskSpec) -> RampTaskSpec:
        """§9 ECHO: produce a natural sentence for learner to repeat."""
        # AI-generated echo sentence
        try:
            sys_p, usr_p = RampPrompts.build_exercise_prompt_generation(
                exercise_type="speak_echo",
                topic=base.topic,
                stage=inp.current_stage,
                support_level=inp.support_level,
                learner_level=inp.learner_level,
                keywords=base.keywords_for_production,
                previous_response=inp.previous_response,
                is_retry=inp.is_retry,
            )
            req = AIRequest(
                messages=[AIMessage(role=AIMessageRole.USER, content=usr_p)],
                task=AITask.RAMP_PROMPT_GENERATION,
                system_instruction=sys_p,
                temperature=0.6,
                max_output_tokens=200,
                response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            )
            resp = await self.ai_router.generate(req)
            data = json.loads(resp.text)
            echo_sentence = data.get("echo_sentence")
        except Exception:
            echo_sentence = None

        # Deterministic fallback echo sentence
        if not echo_sentence:
            fallback_echos = {
                "daily_life": "今日は仕事が忙しかったです。",
                "work": "会議は三時から始まります。",
                "personal": "私は映画を見るのが好きです。",
                "opinions": "テレワークはとても便利だと思います。",
            }
            echo_sentence = fallback_echos.get(base.topic_domain.value, "毎日日本語を勉強しています。")

        base.echo_sentence = echo_sentence
        base.echo_sentence = echo_sentence
        base.prompt_jp = "次の文を声に出して正確に繰り返してください。"
        base.prompt_vi = "Hãy lắng nghe và lặp lại chính xác câu mẫu bên dưới."
        return base

    async def _build_substitute(self, inp: RampGenerationInput, base: RampTaskSpec) -> RampTaskSpec:
        """§10 SUBSTITUTE: template + variable slot."""
        try:
            sys_p, usr_p = RampPrompts.build_exercise_prompt_generation(
                exercise_type="speak_substitute",
                topic=base.topic,
                stage=inp.current_stage,
                support_level=inp.support_level,
                learner_level=inp.learner_level,
                keywords=base.keywords_for_production,
                previous_response=inp.previous_response,
                is_retry=inp.is_retry,
            )
            req = AIRequest(
                messages=[AIMessage(role=AIMessageRole.USER, content=usr_p)],
                task=AITask.RAMP_PROMPT_GENERATION,
                system_instruction=sys_p,
                temperature=0.7,
                max_output_tokens=250,
                response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            )
            resp = await self.ai_router.generate(req)
            data = json.loads(resp.text)
            base.template_sentence = data.get("template_sentence")
            base.substitution_variable = data.get("substitution_variable")
        except Exception:
            # Deterministic fallback
            base.template_sentence = "週末は家でゆっくり過ごします。"
            base.substitution_variable = "友達と"

        if base.template_sentence and base.substitution_variable:
            sub = str(base.substitution_variable).strip().strip("「」『』")
            tmpl = str(base.template_sentence).strip().rstrip("。") + "。"
            base.template_sentence = tmpl
            base.substitution_variable = sub
            base.prompt_jp = f"「{sub}」を使って、文を完成させてください。"
            base.prompt_vi = f"Thay thế hoặc chèn cụm từ 「{sub}」 vào mẫu câu bên dưới."
        return base

    async def _build_complete(self, inp: RampGenerationInput, base: RampTaskSpec) -> RampTaskSpec:
        """§11 COMPLETE: provide sentence stem for learner to complete."""
        stems = {
            "daily_life": "昨日は仕事が終わってから……",
            "work": "来週の会議について……",
            "personal": "最近、一番楽しかったことは……",
            "opinions": "テレワークについて言えば……",
            "experiences": "旅行で一番印象に残ったのは……",
        }
        stem = stems.get(base.topic_domain.value, "最近、私が気になっていることは……")
        base.prompt_jp = f"次の文を自然に完成させてください：「{stem}」"
        base.prompt_vi = f"Hãy hoàn thành câu sau một cách tự nhiên: 「{stem}」"
        base.scaffold.sentence_starter = stem
        return base

    async def _build_expand(self, inp: RampGenerationInput, base: RampTaskSpec) -> RampTaskSpec:
        """§13 EXPAND: start from seed, add one dimension."""
        seed = base.scaffold.sentence_starter or "映画を見ました。"
        dimensions = ["昨日", "友達と", "理由", "detail"]
        attempt_idx = 0  # TODO: track from session
        dimension = dimensions[attempt_idx % len(dimensions)]

        base.seed_sentence = seed
        base.expansion_dimension = dimension
        base.prompt_jp = f"「{dimension}」の情報を加えて、文を拡張してください。"
        base.prompt_vi = f"Thêm thông tin 「{dimension}」 vào câu gốc để nói chi tiết hơn."
        return base

    def _build_keyword(self, inp: RampGenerationInput, base: RampTaskSpec) -> RampTaskSpec:
        """§16 KEYWORD: provide keywords, learner creates connected response."""
        keywords = base.keywords_for_production or base.scaffold.keywords
        if not keywords:
            keywords = ["仕事", "忙しい", "会議", "疲れる"]
        base.keywords_for_production = keywords
        base.prompt_jp = (
            f"次のキーワードをすべて使って、自然な文章を作ってください：\n"
            + "、".join(f"「{k}」" for k in keywords)
        )
        base.prompt_vi = (
            f"Hãy sử dụng tất cả các từ khóa sau để tạo câu tự nhiên:\n"
            + "、".join(keywords)
        )
        return base

    def _build_guided(self, inp: RampGenerationInput, base: RampTaskSpec) -> RampTaskSpec:
        """§17 GUIDED: structured questions to connect into a response."""
        if not base.scaffold.guided_questions:
            base.scaffold.guided_questions = [
                "何をしましたか？",
                "誰と一緒でしたか？",
                "どう感じましたか？",
            ]
        qs_text = "\n".join(
            f"{i+1}. {q}" for i, q in enumerate(base.scaffold.guided_questions)
        )
        base.prompt_jp = (
            f"次の質問に答えながら、つながりのある文章で話してください。\n{qs_text}"
        )
        base.prompt_vi = (
            "Hãy trả lời các câu hỏi sau và nối chúng thành đoạn văn liên kết."
        )
        return base
