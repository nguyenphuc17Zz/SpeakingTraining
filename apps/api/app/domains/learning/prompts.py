import json
from typing import Any

from app.domains.learning.contracts import LearnerLearningState, PriorityScore


class LearningPrompts:
    """Versioned prompt blueprints for AI exercise generation, evaluation, and recommendation explanations."""

    GEN_PROMPT_VERSION = "exercise.gen.v1"
    EVAL_PROMPT_VERSION = "exercise.eval.v1"
    REC_PROMPT_VERSION = "recommendation.explain.v1"
    REFLEX_GEN_PROMPT_VERSION = "reflex.gen.v1"
    REFLEX_EVAL_PROMPT_VERSION = "reflex.eval.v1"
    KEIGO_GEN_PROMPT_VERSION = "keigo.gen.v1"
    KEIGO_EVAL_PROMPT_VERSION = "keigo.eval.v1"
    PITCH_GEN_PROMPT_VERSION = "pitch.gen.v1"
    PITCH_EVAL_PROMPT_VERSION = "pitch.eval.v1"
    SITUATIONAL_GEN_PROMPT_VERSION = "situational.gen.v1"
    SITUATIONAL_EVAL_PROMPT_VERSION = "situational.eval.v1"

    @classmethod
    def build_exercise_generation_prompt(
        cls,
        priority: PriorityScore,
        state: LearnerLearningState,
        template_info: dict[str, Any],
        recent_topics: list[str] | None = None,
    ) -> tuple[str, str]:
        """Returns (system_instruction, user_content) for AI exercise personalization."""
        system_instruction = (
            "Bạn là chuyên gia sư phạm thiết kế bài luyện nói tiếng Nhật (Japanese Speaking Coach). "
            "Nhiệm vụ của bạn là cá nhân hóa bài tập luyện nói dựa trên thông tin trọng tâm và mẫu khung cho trước. "
            "QUY TẮC BẮT BUỘC:\n"
            "1. Tiếng Nhật sử dụng phải 100% tự nhiên, chuẩn ngữ pháp, phù hợp với trình độ học viên.\n"
            "2. Mục tiêu bài tập phải rõ ràng, tạo cơ hội tự nhiên để người học nói cấu trúc/từ vựng mục tiêu.\n"
            "3. Không tiết lộ toàn bộ câu trả lời hoàn chỉnh trong phần hướng dẫn/tình huống.\n"
            "4. Định dạng trả về BẮT BUỘC là JSON hợp lệ theo schema sau, không thêm lời giải thích ngoài JSON:\n"
            "{\n"
            '  "title": "Tiêu đề bài tập ngắn gọn, hấp dẫn bằng tiếng Việt",\n'
            '  "objective": "Mục tiêu cụ thể người học cần đạt được",\n'
            '  "scenario": "Mô tả ngắn gọn bối cảnh tình huống hội thoại (bằng tiếng Việt)",\n'
            '  "instructions": "Hướng dẫn chi tiết cách người học cần phản xạ hoặc đối đáp",\n'
            '  "constraints": ["Quy tắc hoặc ràng buộc, ví dụ: Không dùng câu ngắn cụt lủn"],\n'
            '  "target_patterns": ["Mẫu câu hoặc từ vựng tiếng Nhật trọng tâm cần xuất hiện, ví dụ: わけではない"],\n'
            '  "acceptable_variants": ["Các biến thể ngữ pháp/cách nói tương đương được chấp nhận"],\n'
            '  "scaffold_hint": "Gợi ý mẫu câu mở đầu hoặc từ khóa nếu người học cần trợ giúp",\n'
            '  "estimated_minutes": 5\n'
            "}"
        )

        user_content = (
            f"<exercise_context>\n"
            f"Trọng tâm cần luyện: {priority.title} (Loại: {priority.item_type.value})\n"
            f"Trình độ học viên: {state.overall_level.upper()} (Khả năng nói: {state.speaking_level.upper()})\n"
            f"Mục tiêu người học: {', '.join(state.active_goals) if state.active_goals else 'Giao tiếp công việc & đời sống'}\n"
            f"Độ khó bài tập: {priority.difficulty.value.upper()}\n"
            f"Dạng bài tập: {priority.recommended_exercise_type.value}\n"
            f"Mẫu khung gợi ý: {template_info.get('scenario_template', '')}\n"
            f"Các chủ đề gần đây cần TRÁNH lặp lại: {', '.join(recent_topics or ['Không có'])}\n"
            f"</exercise_context>"
        )

        return system_instruction, user_content

    @classmethod
    def build_exercise_evaluation_prompt(
        cls,
        exercise_title: str,
        exercise_objective: str,
        target_patterns: list[str],
        user_transcript: str,
        context_notes: str | None = None,
    ) -> tuple[str, str]:
        """Returns (system_instruction, user_content) for AI exercise evaluation."""
        system_instruction = (
            "Bạn là giám khảo đánh giá kỹ năng nói tiếng Nhật phản xạ. "
            "Hãy đánh giá lượt nói của học viên dựa trên mục tiêu bài tập và các mẫu câu/từ vựng mục tiêu. "
            "QUY TẮC ĐÁNH GIÁ:\n"
            "1. Kiểm tra xem người học có sử dụng đúng ngữ pháp, tự nhiên và đạt được mục tiêu giao tiếp không.\n"
            "2. Chấp nhận các biến thể diễn đạt phong phú, không bắt buộc người học phải nói y hệt một đáp án duy nhất.\n"
            "3. Không tự ý bịa đặt số liệu thống kê hoặc thay đổi thang điểm.\n"
            "4. Trả về định dạng JSON hợp lệ theo schema sau:\n"
            "{\n"
            '  "success": true,\n'
            '  "score": 85,\n'
            '  "target_usage": "correct",\n'
            '  "grammar_score": 90,\n'
            '  "naturalness_score": 80,\n'
            '  "confidence": 0.90,\n'
            '  "feedback": "Nhận xét sư phạm ngắn gọn, tích cực bằng tiếng Việt (2-3 câu)",\n'
            '  "evidence": ["Trích dẫn cụ thể điểm tốt hoặc điểm cần cải thiện trong câu của học viên"]\n'
            "}"
        )

        user_content = (
            f"<exercise_data>\n"
            f"Bài tập: {exercise_title}\n"
            f"Mục tiêu: {exercise_objective}\n"
            f"Mẫu cấu trúc mục tiêu: {', '.join(target_patterns)}\n"
            f"Ngữ cảnh: {context_notes or 'Hội thoại giao tiếp'}\n"
            f"Câu nói thực tế của học viên: {user_transcript}\n"
            f"</exercise_data>"
        )

        return system_instruction, user_content

    @classmethod
    def build_reflex_generation_prompt(
        cls,
        sub_mode: str,
        priority: PriorityScore,
        state: LearnerLearningState,
        template_info: dict[str, Any],
        pressure_level: str = "normal",
        timer_ms: int = 4000,
        verb: str | None = None,
        conjugation_target: str | None = None,
    ) -> tuple[str, str]:
        """Reflex-specific generation prompt (converts to generic but tags reflex)."""
        base_sys, base_user = cls.build_exercise_generation_prompt(priority, state, template_info)
        reflex_addon = (
            f"\nBỔ SUNG REFLEX ({sub_mode}):\n"
            f"- Pressure: {pressure_level} ({timer_ms}ms timer)\n"
            f"- Sub-mode: {sub_mode} — Think less. Speak faster. Không tạo worksheet ngữ pháp.\n"
            f"- Timer là công cụ, không phải mục tiêu duy nhất; correctness > speed.\n"
        )
        if verb:
            reflex_addon += f"- Động từ mục tiêu: {verb} → {conjugation_target or 'tự chọn'}\n"
        reflex_addon += "- Tạo prompt ngắn gọn, tự nhiên, phù hợp level, và phải có acceptable_variants nếu có nhiều đáp án đúng.\n"
        return base_sys + reflex_addon, base_user + reflex_addon

    @classmethod
    def build_reflex_evaluation_prompt(
        cls,
        sub_mode: str,
        prompt: str,
        user_transcript: str,
        expected: str | None = None,
        semantic_target: dict[str, Any] | None = None,
        reaction_latency_ms: float | None = None,
        timer_limit_ms: int | None = None,
    ) -> tuple[str, str]:
        sys = (
            "Bạn là giám khảo REFLEX tiếng Nhật — đánh giá phản xạ nói dưới áp lực thời gian. "
            "Phải xét: reaction latency, correctness, context_fit, naturalness, completeness, independence. "
            "Không đánh đồng 'nhanh = giỏi' hay 'chậm = kém'. "
            "Chấp nhận nhiều cách diễn đạt tự nhiên, informal ≠ lỗi. "
            "Trả về JSON: {success, score, grammar_score, naturalness_score, context_fit, completeness, confidence, feedback, evidence}"
        )
        user = (
            f"<reflex_eval>\n"
            f"Sub-mode: {sub_mode}\n"
            f"Prompt: {prompt}\n"
            f"Expected: {expected or 'open-ended'}\n"
            f"Semantic target: {semantic_target}\n"
            f"User transcript: {user_transcript}\n"
            f"Reaction: {reaction_latency_ms}ms / timer {timer_limit_ms}ms\n"
            f"</reflex_eval>"
        )
        return sys, user

    @classmethod
    def build_keigo_generation_prompt(
        cls,
        sub_mode: str,
        priority: PriorityScore,
        state: LearnerLearningState,
        template_info: dict[str, Any],
        pressure_level: str = "normal",
        timer_ms: int = 5000,
        social_context: dict[str, Any] | None = None,
    ) -> tuple[str, str]:
        base_sys, base_user = cls.build_exercise_generation_prompt(priority, state, template_info)
        keigo_addon = (
            f"\nBỔ SUNG KEIGO ({sub_mode}):\n"
            f"- Pressure: {pressure_level} ({timer_ms}ms)\n"
            f"- Social context: {social_context}\n"
            f"- Phải tạo tình huống Uchi/Soto rõ ràng, đúng hướng kính ngữ, tự nhiên, không cứng nhắc giáo trình.\n"
            f"- acceptable_variants phải chứa các biến thể tự nhiên (nếu có).\n"
        )
        return base_sys + keigo_addon, base_user + keigo_addon

    @classmethod
    def build_keigo_evaluation_prompt(
        cls,
        sub_mode: str,
        prompt: str,
        user_transcript: str,
        expected: str | None = None,
        social_context: dict[str, Any] | None = None,
        linguistic_analysis: dict[str, Any] | None = None,
        reaction_latency_ms: float | None = None,
        timer_limit_ms: int | None = None,
    ) -> tuple[str, str]:
        sys = (
            "Bạn là giám khảo KÍNH NGỮ tiếng Nhật — đánh giá Uchi/Soto, register, keigo, naturalness, context. "
            "Phân biệt GRAMMATICALY_CORRECT vs CONTEXTUALLY_AWKWARD, double keigo nuanced, over/under formal. "
            "Chấp nhận nhiều đáp án tự nhiên, không phạt variant hợp lệ. "
            "Trả về JSON: {success, score, grammar_score, naturalness_score, context_fit, register_accuracy, keigo_accuracy, role_accuracy, completeness, confidence, feedback, evidence, double_keigo:{status, severity}}"
        )
        user = (
            f"<keigo_eval>\n"
            f"Sub-mode: {sub_mode}\n"
            f"Prompt: {prompt}\n"
            f"Expected: {expected or 'open'}\n"
            f"SocialContext: {social_context}\n"
            f"Linguistic: {linguistic_analysis}\n"
            f"User: {user_transcript}\n"
            f"Reaction: {reaction_latency_ms}ms / {timer_limit_ms}ms\n"
            f"</keigo_eval>"
        )
        return sys, user

    @classmethod
    def build_pitch_generation_prompt(
        cls,
        sub_mode: str,
        priority: PriorityScore,
        state: LearnerLearningState,
        template_info: dict[str, Any],
        pressure_level: str = "normal",
        timer_ms: int = 5000,
        pitch_pattern: list[str] | None = None,
    ) -> tuple[str, str]:
        base_sys, base_user = cls.build_exercise_generation_prompt(priority, state, template_info)
        pitch_addon = (
            f"\nBỔ SUNG PITCH ({sub_mode}):\n"
            f"- Pressure: {pressure_level} ({timer_ms}ms)\n"
            f"- Pitch pattern: {pitch_pattern}\n"
            f"- Phải tạo minimal pair / mora / contour tự nhiên, không hard-code giant list, dựa trên provider.\n"
            f"- acceptable_variants phải chứa biến thể đọc/cách nói tương đương.\n"
        )
        return base_sys + pitch_addon, base_user + pitch_addon

    @classmethod
    def build_pitch_evaluation_prompt(
        cls,
        sub_mode: str,
        prompt: str,
        user_transcript: str,
        expected: str | None = None,
        pitch_analysis: dict[str, Any] | None = None,
        reaction_latency_ms: float | None = None,
        timer_limit_ms: int | None = None,
    ) -> tuple[str, str]:
        sys = (
            "Bạn là giám khảo CAO ĐỘ tiếng Nhật — đánh giá pitch accent, mora timing, devoicing, naturalness. "
            "Phân biệt lexical pitch vs absolute Hz, mora vs length, devoicing là xu hướng không bắt buộc 100%. "
            "Chấp nhận nhiều đáp án tự nhiên. "
            "Trả về JSON: {success, score, grammar_score, naturalness_score, context_fit, pitch_accuracy, mora_accuracy, completeness, confidence, feedback, evidence}"
        )
        user = (
            f"<pitch_eval>\n"
            f"Sub-mode: {sub_mode}\n"
            f"Prompt: {prompt}\n"
            f"Expected: {expected or 'open'}\n"
            f"PitchAnalysis: {pitch_analysis}\n"
            f"User: {user_transcript}\n"
            f"Reaction: {reaction_latency_ms}ms / {timer_limit_ms}ms\n"
            f"</pitch_eval>"
        )
        return sys, user

    @classmethod
    def build_situational_generation_prompt(
        cls,
        sub_mode: str,
        priority: PriorityScore,
        state: LearnerLearningState,
        template_info: dict[str, Any],
        pressure_level: str = "normal",
        timer_ms: int = 5000,
        situational_context: dict[str, Any] | None = None,
    ) -> tuple[str, str]:
        base_sys, base_user = cls.build_exercise_generation_prompt(priority, state, template_info)
        addon = (
            f"\nBỔ SUNG SITUATIONAL ({sub_mode}):\n"
            f"- Pressure: {pressure_level} ({timer_ms}ms)\n"
            f"- Situational context: {situational_context}\n"
            f"- Phải tạo tình huống có location/role/goal/constraints/props/event_pool đa dạng, không hard-code giant сценарий.\n"
        )
        return base_sys + addon, base_user + addon

    @classmethod
    def build_situational_evaluation_prompt(
        cls,
        sub_mode: str,
        prompt: str,
        user_transcript: str,
        expected: str | None = None,
        situational_context: dict[str, Any] | None = None,
        reaction_latency_ms: float | None = None,
        timer_limit_ms: int | None = None,
    ) -> tuple[str, str]:
        sys = (
            "Bạn là giám khảo TÌNH HUỐNG tiếng Nhật — đánh giá intent, entity, dialogue act, task completion, naturalness, register. "
            "Chấp nhận nhiều cách diễn đạt tự nhiên, miễn là intent/entity đúng và phù hợp ngữ cảnh. "
            "Trả về JSON: {success, score, grammar_score, naturalness_score, context_fit, intent_accuracy, task_completion, completeness, confidence, feedback, evidence}"
        )
        user = (
            f"<situational_eval>\n"
            f"Sub-mode: {sub_mode}\n"
            f"Prompt: {prompt}\n"
            f"Expected: {expected or 'open'}\n"
            f"Context: {situational_context}\n"
            f"User: {user_transcript}\n"
            f"Reaction: {reaction_latency_ms}ms / {timer_limit_ms}ms\n"
            f"</situational_eval>"
        )
        return sys, user

    @classmethod
    def build_recommendation_explanation_prompt(
        cls,
        priority_title: str,
        priority_reason: str,
        mastery_pct: int,
        attempt_count: int,
        success_count: int,
        active_goal: str,
    ) -> tuple[str, str]:
        """Returns prompt to turn deterministic statistics into user-friendly motivational explanation."""
        system_instruction = (
            "Bạn là Japanese Speaking Coach. Hãy giải thích ngắn gọn (2 câu bằng tiếng Việt) lý do tại sao hôm nay người học nên luyện kỹ năng này. "
            "QUY TẮC: Tuyệt đối chỉ sử dụng các số liệu thực tế được cung cấp trong thẻ <stats>, không bịa thêm số liệu."
        )

        user_content = (
            f"<stats>\n"
            f"Kỹ năng: {priority_title}\n"
            f"Lý do tính toán: {priority_reason}\n"
            f"Độ thuần thục hiện tại: {mastery_pct}%\n"
            f"Số lần luyện tập gần đây: {success_count}/{attempt_count} lần thành công\n"
            f"Mục tiêu hướng tới: {active_goal}\n"
            f"</stats>"
        )

        return system_instruction, user_content
