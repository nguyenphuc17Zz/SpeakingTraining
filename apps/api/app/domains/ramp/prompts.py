"""RampPrompts — versioned AI prompts for Mode 6 tasks.

§44 AI Generation: RAMP_TOPIC_GENERATION, RAMP_PROMPT_GENERATION,
RAMP_FOLLOWUP_GENERATION, RAMP_HINT_GENERATION, RAMP_SEMANTIC_EVALUATION, RAMP_FEEDBACK.
§45 AI Constraints: must preserve learner level, stage, support level, task difficulty.
§47 No hard-coded answer bank — semantic evaluation only.
"""

from __future__ import annotations

from typing import Any


class RampPrompts:
    """Versioned prompt builders for all Mode 6 AI tasks."""

    TOPIC_GEN_VERSION = "ramp.topic.v1"
    PROMPT_GEN_VERSION = "ramp.prompt.v1"
    FOLLOWUP_GEN_VERSION = "ramp.followup.v1"
    HINT_GEN_VERSION = "ramp.hint.v1"
    SEMANTIC_EVAL_VERSION = "ramp.eval.v1"
    FEEDBACK_GEN_VERSION = "ramp.feedback.v1"

    # ---------------------------------------------------------------------------
    # §44 RAMP_TOPIC_GENERATION
    # ---------------------------------------------------------------------------

    @classmethod
    def build_topic_generation_prompt(
        cls,
        stage: int,
        support_level: int,
        learner_level: str,
        measured_speaking_level: str,
        topic_domain: str,
        interests: list[str],
        topic_history: list[str],
        desired_duration_sec: int,
    ) -> tuple[str, str]:
        system = (
            "You are a Japanese speaking coach designing practice topics for output rehabilitation.\n"
            "RULES:\n"
            "1. Generate ONE topic appropriate for the stage and measured speaking level (NOT JLPT level).\n"
            "2. Stage 0–4: use very simple, concrete daily situations. Stage 5+: richer context.\n"
            "3. Do NOT generate grammar explanations or vocabulary lists — only the topic+prompt.\n"
            "4. Return ONLY valid JSON with this schema:\n"
            "{\n"
            '  "topic": "Short topic label in Japanese",\n'
            '  "topic_vi": "Vietnamese topic label",\n'
            '  "prompt_jp": "The Japanese instruction/question shown to the learner",\n'
            '  "prompt_vi": "Vietnamese explanation of what to do",\n'
            '  "domain": "one of: personal/daily_life/work/study/opinions/preferences/experiences/hypothetical/comparison/problem_solving",\n'
            '  "keywords": ["keyword1", "keyword2"],\n'
            '  "sentence_starter": "Optional Japanese sentence starter (or null)",\n'
            '  "example_response": "Optional example answer (only for support_level>=6, else null)",\n'
            '  "difficulty_note": "Why this difficulty is appropriate"\n'
            "}"
        )
        user = (
            f"Generate a Mode 6 speaking ramp topic.\n"
            f"Stage: {stage}/10 (0=echo repetition, 10=60s independent speech)\n"
            f"JLPT Level: {learner_level} | Measured speaking level: {measured_speaking_level}\n"
            f"Support level: {support_level}/7 (0=no support, 7=full translation)\n"
            f"Topic domain: {topic_domain}\n"
            f"Target duration: {desired_duration_sec}s\n"
            f"Learner interests: {', '.join(interests) if interests else 'general'}\n"
            f"Recent topics to AVOID: {', '.join(topic_history[-5:]) if topic_history else 'none'}\n"
            f"Generate a fresh, natural topic. The prompt_jp must be in natural Japanese."
        )
        return system, user

    # ---------------------------------------------------------------------------
    # §44 RAMP_PROMPT_GENERATION (exercise-type-specific prompt)
    # ---------------------------------------------------------------------------

    @classmethod
    def build_exercise_prompt_generation(
        cls,
        exercise_type: str,
        topic: str,
        stage: int,
        support_level: int,
        learner_level: str,
        keywords: list[str],
        previous_response: str | None,
        is_retry: bool,
    ) -> tuple[str, str]:
        system = (
            "You are generating a specific speaking ramp exercise prompt in Japanese.\n"
            "RULES:\n"
            "1. The prompt must be natural Japanese appropriate for the exercise type.\n"
            "2. Do NOT reveal the expected answer in the prompt.\n"
            "3. For retry, vary the surface form but test the same skill.\n"
            "4. Return ONLY valid JSON:\n"
            "{\n"
            '  "prompt_jp": "The Japanese prompt/question for the learner",\n'
            '  "template_sentence": "For substitute exercises: the template sentence or null",\n'
            '  "substitution_variable": "The word/phrase to substitute, or null",\n'
            '  "seed_sentence": "For expand exercises: the seed to expand, or null",\n'
            '  "expansion_dimension": "時間/人/場所/理由/detail or null",\n'
            '  "echo_sentence": "For echo exercises: exact sentence to repeat, or null",\n'
            '  "scaffold_hint_jp": "A hint in Japanese that does NOT give the answer"\n'
            "}"
        )
        retry_note = " (This is a RETRY — vary surface form, keep same skill)" if is_retry else ""
        prev_note = f"\nPrevious learner response: 「{previous_response}」" if previous_response else ""
        user = (
            f"Generate a {exercise_type} exercise prompt.{retry_note}\n"
            f"Topic: {topic}\n"
            f"Stage: {stage}/10 | Support level: {support_level}/7\n"
            f"Learner JLPT: {learner_level}\n"
            f"Keywords: {', '.join(keywords) if keywords else 'none'}"
            f"{prev_note}"
        )
        return system, user

    # ---------------------------------------------------------------------------
    # §44 RAMP_FOLLOWUP_GENERATION
    # ---------------------------------------------------------------------------

    @classmethod
    def build_followup_generation_prompt(
        cls,
        user_response: str,
        topic: str,
        stage: int,
        previous_followups: list[str],
        current_depth: int,
    ) -> tuple[str, str]:
        """§50 FollowUpGenerator — must inspect actual previous response."""
        system = (
            "You are generating a contextual follow-up question for a Japanese speaking exercise.\n"
            "RULES:\n"
            "1. The follow-up MUST relate to content in the learner's actual response.\n"
            "2. Follow depth progression: fact(1) → why(2) → example(3) → comparison(4) → hypothetical(5).\n"
            "3. Do NOT ask about something not mentioned or implied by the response.\n"
            "4. Stay on the same topic — do NOT jump to a new topic.\n"
            "5. Return ONLY valid JSON:\n"
            "{\n"
            '  "question_jp": "The Japanese follow-up question",\n'
            '  "question_vi": "Vietnamese translation of the question",\n'
            '  "follow_up_type": "fact|why|example|comparison|hypothetical",\n'
            '  "depth_level": 1,\n'
            '  "relates_to": "the specific keyword/phrase from the response this question builds on"\n'
            "}"
        )
        depth_map = {1: "fact", 2: "why", 3: "example", 4: "comparison", 5: "hypothetical"}
        target_type = depth_map.get(current_depth, "why")
        prev_note = f"\nPrevious follow-ups asked: {'; '.join(previous_followups[-3:])}" if previous_followups else ""
        user = (
            f"Generate a follow-up question (depth {current_depth}: {target_type}).\n"
            f"Topic: {topic}\n"
            f"Stage: {stage}/10\n"
            f"Learner's response: 「{user_response}」"
            f"{prev_note}\n"
            "Generate a meaningful follow-up that deepens this specific topic."
        )
        return system, user

    # ---------------------------------------------------------------------------
    # §44 RAMP_HINT_GENERATION
    # ---------------------------------------------------------------------------

    @classmethod
    def build_hint_generation_prompt(
        cls,
        exercise_type: str,
        topic: str,
        prompt_jp: str,
        elaboration_signal: str,
        hint_step: int,
    ) -> tuple[str, str]:
        """§20 Progressive hints that do NOT reveal the answer."""
        system = (
            "You are generating a progressive hint for a Japanese speaking exercise.\n"
            "CRITICAL: The hint must NOT give the answer. It gives a cognitive cue only.\n"
            "Hint steps: 1=add detail, 2=add reason, 3=give example structure, 4=compare.\n"
            "Return ONLY valid JSON:\n"
            "{\n"
            '  "hint_jp": "Japanese hint cue for the learner",\n'
            '  "hint_vi": "Vietnamese explanation of the hint"\n'
            "}"
        )
        user = (
            f"Generate hint step {hint_step} for a {exercise_type} exercise.\n"
            f"Topic: {topic}\n"
            f"Original prompt: {prompt_jp}\n"
            f"Issue detected: {elaboration_signal}\n"
            f"The hint should prompt the learner to {hint_step == 1 and 'add one detail' or hint_step == 2 and 'explain why' or hint_step == 3 and 'give an example' or 'compare with something else'}."
        )
        return system, user

    # ---------------------------------------------------------------------------
    # §44 RAMP_SEMANTIC_EVALUATION
    # ---------------------------------------------------------------------------

    @classmethod
    def build_semantic_evaluation_prompt(
        cls,
        topic: str,
        prompt_jp: str,
        exercise_type: str,
        stage: int,
        user_transcript: str,
        support_level: int,
    ) -> tuple[str, str]:
        """§46 AI evaluates: semantic adequacy, naturalness, sample answers (3 styles), and coaching advice."""
        system = (
            "You are an expert Japanese speaking coach evaluating an oral output attempt.\n"
            "RULES:\n"
            "1. Accept ANY grammatically valid, semantically relevant Japanese response.\n"
            "2. Evaluate naturalness of actual spoken Japanese.\n"
            "3. Generate 3 DISTINCT suggested sample answers suitable for this exercise:\n"
            "   - 'casual': Natural, everyday spoken Japanese (Thường ngày).\n"
            "   - 'polite': Standard polite/business form (Lịch sự / Công sở - です/ます).\n"
            "   - 'advanced': Richer, extended answer with reasons or examples (Mở rộng nâng cao).\n"
            "4. Provide constructive coaching advice in Vietnamese to help the learner build speaking confidence and reflex.\n"
            "5. Return ONLY valid JSON:\n"
            "{\n"
            '  "semantic_relevance": 0-100,\n'
            '  "naturalness": 0-100,\n'
            '  "grammar_score": 0-100,\n'
            '  "completeness": 0-100,\n'
            '  "idea_quality": 0-100,\n'
            '  "has_reason": true|false,\n'
            '  "has_example": true|false,\n'
            '  "sentence_complete": true|false,\n'
            '  "errors": [{"fragment": "...", "correction": "...", "note": "..."}],\n'
            '  "strengths": ["Điểm nói tốt 1 (tiếng Việt)", "Điểm nói tốt 2"],\n'
            '  "correction_jp": "Minimal correction in Japanese if needed (or null)",\n'
            '  "feedback_jp": "One line of feedback in Japanese",\n'
            '  "sample_answers": [\n'
            '    {\n'
            '      "style": "casual",\n'
            '      "style_label": "Thường ngày",\n'
            '      "japanese": "Natural Japanese sentence",\n'
            '      "vietnamese": "Bản dịch tiếng Việt",\n'
            '      "nuance": "Sắc thái thân mật, tự nhiên khi nói chuyện bạn bè"\n'
            '    },\n'
            '    {\n'
            '      "style": "polite",\n'
            '      "style_label": "Lịch sự công sở",\n'
            '      "japanese": "Polite Japanese sentence with desu/masu",\n'
            '      "vietnamese": "Bản dịch tiếng Việt",\n'
            '      "nuance": "Lịch sự, trang nhã, phù hợp giao tiếp văn phòng"\n'
            '    },\n'
            '    {\n'
            '      "style": "advanced",\n'
            '      "style_label": "Mở rộng nâng cao",\n'
            '      "japanese": "Extended Japanese sentence with reason/example",\n'
            '      "vietnamese": "Bản dịch tiếng Việt",\n'
            '      "nuance": "Bổ sung liên từ và lý do để phát triển ý sâu sắc"\n'
            '    }\n'
            '  ],\n'
            '  "coaching_advice": {\n'
            '    "overall_comment": "Nhận xét tổng thể bằng tiếng Việt...",\n'
            '    "strengths": ["Điểm phát huy tốt 1", "Điểm phát huy tốt 2"],\n'
            '    "improvements": ["Lời khuyên bứt phá 1", "Lời khuyên bứt phá 2"],\n'
            '    "grammar_notes": ["Ghi chú cấu trúc ngữ pháp/trợ từ..."]\n'
            '  },\n'
            '  "confidence": 0.0-1.0\n'
            "}"
        )
        user = (
            f"Evaluate this Japanese response.\n"
            f"Exercise type: {exercise_type} | Stage: {stage}/10\n"
            f"Topic: {topic}\n"
            f"Prompt given: 「{prompt_jp}」\n"
            f"Support level used: {support_level}/7\n"
            f"Learner's response: 「{user_transcript}」\n"
            "Provide accurate scores, 3 diverse sample answers, and insightful coaching advice."
        )
        return system, user

    # ---------------------------------------------------------------------------
    # §44 RAMP_FEEDBACK
    # ---------------------------------------------------------------------------

    @classmethod
    def build_feedback_prompt(
        cls,
        topic: str,
        user_transcript: str,
        ramp_score: dict[str, Any],
        stage: int,
        elaboration_signals: list[str],
    ) -> tuple[str, str]:
        """§37 Immediate structured feedback — badges + next action."""
        system = (
            "You are providing immediate speaking feedback for a Japanese output rehabilitation exercise.\n"
            "RULES:\n"
            "1. Be encouraging — this learner is rebuilding speaking confidence.\n"
            "2. Prioritize: incomplete sentence > grammar blocking meaning > lack of elaboration > minor issues.\n"
            "3. Give at most 2 correction points per attempt.\n"
            "4. The 'next_cue' must be one actionable Japanese instruction.\n"
            "Return ONLY valid JSON:\n"
            "{\n"
            '  "badges": ["✅ 意味が伝わった", "✅ 文法OK", "⚠️ 短すぎ", "🎯 理由を足してみよう"],\n'
            '  "main_feedback_jp": "One encouraging sentence in Japanese",\n'
            '  "main_feedback_vi": "Vietnamese translation",\n'
            '  "next_cue_jp": "One Japanese instruction for the retry",\n'
            '  "next_action": "retry|next|elaborate"\n'
            "}"
        )
        user = (
            f"Stage {stage}/10 — Topic: {topic}\n"
            f"Learner said: 「{user_transcript}」\n"
            f"Scores: {ramp_score}\n"
            f"Issues detected: {', '.join(elaboration_signals) if elaboration_signals else 'none'}\n"
            "Generate immediate, concise feedback with badges."
        )
        return system, user
