"""Monologue prompts — dynamic generation, never hard-coded topic lists."""

from __future__ import annotations

from typing import Any

from app.domains.monologue.contracts import SpeechGenre, SpeechSupportLevel, SpeechTopicDomain


class MonologuePrompts:
    GEN_PROMPT_VERSION = "monologue.gen.v1"
    EVAL_PROMPT_VERSION = "monologue.eval.v1"
    NATIVE_UPGRADE_VERSION = "monologue.upgrade.v1"

    @classmethod
    def build_generation_prompt(
        cls,
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
        seed: str | None = None,
    ) -> tuple[str, str]:
        # VI+JP hybrid per user choice: topic in Vietnamese-friendly JP, instruction in JP
        system_instruction = (
            "Bạn là chuyên gia thiết kế bài luyện Monologue tiếng Nhật (Mode 5 - 1分間スピーチ). "
            "Nhiệm vụ: tạo MỘT chủ đề nói MỚI, speakable, cấp độ phù hợp, không trùng lặp. "
            "QUY TẮC BẮT BUỘC:\n"
            "1. Topic phải relevant, age-appropriate, level-appropriate, không đòi hỏi kiến thức bách khoa hiếm.\n"
            "2. Không sao chép topic gần đây. Sáng tạo góc nhìn mới.\n"
            "3. Instruction phải bằng TIẾNG NHẬT tự nhiên (keigo nếu genre business/interview).\n"
            "4. Constraints là learning primitives do hệ thống cung cấp — không tự bịa constraint mới ngoài list.\n"
            "5. VI+JP hybrid: topic có thể hiển thị tiếng Việt/JP ngắn gọn, nhưng instruction_ja bắt buộc tiếng Nhật.\n"
            "6. Trả về JSON hợp lệ duy nhất, không thêm lời giải thích ngoài JSON:\n"
            "{\n"
            '  \"topic\": \"Chủ đề ngắn gọn (VI hoặc JP, 5-12 từ)\",\n'
            '  \"instruction\": \"指示（日本語、自然）\",\n'
            '  \"instruction_ja\": \"同上、日本語\",\n'
            '  \"constraints\": [\"include_one_example\", ...],\n'
            '  \"keywords\": [\"キーワード1\", ...],\n'
            '  \"outline\": [\"導入\", \"本論\", ...],\n'
            '  \"guided_questions\": [\"質問1\", ...],\n'
            '  \"learning_targets\": [\"coherence\"],\n'
            '  \"difficulty\": 3,\n'
            '  \"expected_duration_sec\": 60,\n'
            '  \"prep_duration_sec\": 30\n'
            "}\n"
            "QUAN TRỌNG: Không hard-code hàng trăm topic trong code — mỗi lần phải sinh topic mới dựa trên domain/genre/interest."
        )

        user_content = (
            f"<monologue_context>\n"
            f"Level: {level.upper()} (Speaking: {speaking_level.upper()})\n"
            f"Genre: {genre.value} | Domain: {domain.value} | Difficulty: {difficulty}/5\n"
            f"Duration: {duration_sec}s | Prep: {prep_sec}s | SupportLevel: {support_level.value} ({support_level.name})\n"
            f"Constraints hệ thống: {', '.join(constraints)}\n"
            f"Interests: {', '.join(interests) if interests else 'không có'}\n"
            f"Career: {career_domain or 'chung'}\n"
            f"Weaknesses: {weaknesses[:3] if weaknesses else 'không có'}\n"
            f"Recent topics TRÁNH lặp: {', '.join(recent_topics[-10:]) if recent_topics else 'không có'}\n"
            f"Seed: {seed or 'none'}\n"
            f"</monologue_context>\n"
            f"YÊU CẦU: Tạo 1 topic MỚI thuộc domain {domain.value}, genre {genre.value}, "
            f"thời lượng {duration_sec}s, mức khó {difficulty}, constraints {constraints}."
        )
        return system_instruction, user_content

    @classmethod
    def build_evaluation_prompt(
        cls,
        genre: SpeechGenre,
        topic: str,
        instruction: str,
        constraints: list[str],
        transcript: str,
        deterministic_context: dict[str, Any],
        duration_sec: int,
    ) -> tuple[str, str]:
        system_instruction = (
            "Bạn là giám khảo Monologue tiếng Nhật — đánh giá coherence, relevance, naturalness, genre_fit, content, argumentation. "
            "Bạn nhận transcript + deterministic metrics (pause_count, filler_count, duration...) — KHÔNG được bịa lại các số đếm này. "
            "Chỉ diễn giải: 'pauses suggest hesitation' được, 'you had 12 pauses' khi backend đếm 8 là CẤM. "
            "Phân biệt: filler tự nhiên ≠ lỗi nặng; self-repair thành công ≠ breakdown; pause ở discourse boundary ≠ giữa phrase. "
            "Trả về JSON:\n"
            "{\n"
            '  \"relevance\": 85, \"coherence\": 80, \"naturalness\": 82, \"genre_fit\": 88, \"argument_quality\": 75, \"content_score\": 80,\n'
            '  \"main_strength\": \"...\", \"main_weakness\": \"...\",\n'
            '  \"feedback\": [\"2-3 nhận xét sư phạm tiếng Việt\"],\n'
            '  \"confidence\": 0.88\n'
            "}"
        )
        user_content = (
            f"<speech_eval>\n"
            f"Genre: {genre.value} | Topic: {topic} | Instruction: {instruction}\n"
            f"Constraints: {constraints} | Target duration: {duration_sec}s\n"
            f"Transcript: {transcript}\n"
            f"Deterministic (authoritative, do NOT override): {deterministic_context}\n"
            f"</speech_eval>"
        )
        return system_instruction, user_content

    @classmethod
    def build_native_upgrade_prompt(
        cls,
        transcript: str,
        genre: SpeechGenre,
        topic: str,
        level: str,
    ) -> tuple[str, str]:
        system_instruction = (
            "Bạn là biên tập viên tiếng Nhật bản xứ — tạo 2 phiên bản nâng cấp KHÔNG bịa fact mới, giữ stance/meaning của learner. "
            "A) minimal_correction: giữ wording, chỉ sửa lỗi ngữ pháp. "
            "B) native_version: tự nhiên, polished. "
            "C) professional_version: nếu business/interview/presentation thì thêm, else null. "
            "Kèm giải thích: Original → correction → why → native alternative. "
            "Trả về JSON:\n"
            "{\n"
            '  \"minimal_correction\": \"...\",\n'
            '  \"native_version\": \"...\",\n'
            '  \"professional_version\": null,\n'
            '  \"explanations\": [{\"original\": \"...\", \"correction\": \"...\", \"why\": \"...\", \"alternative\": \"...\"}],\n'
            '  \"confidence\": 0.9\n'
            "}"
        )
        user_content = (
            f"<upgrade>\n"
            f"Genre: {genre.value} | Topic: {topic} | Level: {level}\n"
            f"Transcript: {transcript}\n"
            f"</upgrade>"
        )
        return system_instruction, user_content
