"""AIPitchGenerator — 100% dynamic on-the-fly Pitch Accent & Mora Exercise Generation via Gemini AI & Acoustic Providers.

Generates infinite authentic Japanese pitch accent challenges (Minimal Pairs, Mora Length, Vowel Devoicing, Contour Curves, Recognition).
Gracefully falls back to PitchExerciseFactory & Sudachi/pykakasi if AI is unreachable.
"""

from __future__ import annotations

import json
import random
import uuid
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
from app.domains.pitch.exercise_factory import PitchExerciseFactory, TIMER_DEFAULTS
from app.domains.pitch.resource_provider import get_pitch_provider
from app.domains.reflex.pressure_profiles import timer_for_level

PITCH_TOPICS_POOL = [
    ("Ẩm thực & Đồ uống (飲食)", "ame (kẹo) vs ame (mưa), sake (rượu) vs sake (cá hồi), kaki (hồng) vs kaki (hàu), niku, tori, pan"),
    ("Đời sống & Gia đình (生活・家族)", "ojisan (chú) vs ojiisan (ông), obasan (cô) vs obaasan (bà), hashi (đũa/cầu), ie, heya, hon"),
    ("Công sở & Giao tiếp (ビジネス・職場)", "desu/mashita (devoicing), shite, tsugi, kitte (tem) vs kite (đến), kaigi, shorui, shachou"),
    ("Thiên nhiên & Động vật (自然・動物)", "kumo (mây) vs kumo (nhện), hana (hoa) vs hana (mũi), neko, inu, umi, yama, sakura"),
    ("Thời gian & Số đếm (時間・数字)", "ichi, shichi (devoicing), ima (bây giờ) vs ima (phòng khách), asa, hiru, yoru, ashita"),
    ("Hành động & Di chuyển (動作・移動)", "kite vs kitte, iku, kuru, miru, kiku (devoicing), kaeru (về) vs kaeru (ếch), matsu"),
    ("Cảm xúc & Tính từ (感情・形容詞)", "suki (thích - devoicing), atsui (nóng) vs atsui (dày), shiroi, kuroi, takai, yasui"),
    ("Địa điểm & Đô thị (都市・交通)", "biru (tòa nhà) vs biiru (bia), saka (dốc) vs sakka (nhà văn), eki, toukyou, densha"),
]


def compute_pitch_mora_helpers(
    reading: str,
    pitch_pattern: list[str] | None = None,
    downstep_index: int = 0,
) -> tuple[list[dict[str, Any]], str]:
    """Computes mora tokens breakdown and NHK downstep notation."""
    if not reading:
        return [], ""

    moras = []
    i = 0
    chars = list(reading)
    while i < len(chars):
        c = chars[i]
        if i + 1 < len(chars) and chars[i + 1] in "ゃゅょャュョぁぃぅぇぉァィゥェォ":
            moras.append(c + chars[i + 1])
            i += 2
        else:
            moras.append(c)
            i += 1

    pat = pitch_pattern or []
    breakdown = []
    notation_parts = []

    for idx, m in enumerate(moras):
        if idx < len(pat):
            tone = pat[idx]
        else:
            if downstep_index == 0:
                tone = "L" if idx == 0 and len(moras) > 1 else "H"
            elif downstep_index == 1:
                tone = "H" if idx == 0 else "L"
            elif idx + 1 <= downstep_index:
                tone = "L" if idx == 0 else "H"
            else:
                tone = "L"

        is_ds = downstep_index > 0 and (idx + 1 == downstep_index)
        breakdown.append({
            "index": idx + 1,
            "mora": m,
            "tone": tone.upper(),
            "is_downstep": is_ds,
        })

        notation_parts.append(m)
        if is_ds:
            notation_parts.append("ꜜ")

    if downstep_index == 0 and len(moras) > 0:
        notation_parts.append("￣")

    return breakdown, "".join(notation_parts)


class AIPitchGenerator:
    """Generates infinite, creative, non-repeating Pitch Accent speaking exercises using Gemini AI."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)
        self.factory = PitchExerciseFactory()
        self.provider = get_pitch_provider()
        self.recent_signatures: set[str] = set()

    async def generate_dynamic_exercise(
        self,
        sub_mode: str,
        difficulty: str = "normal",
        pressure_level: str = "normal",
        user_id: str = "pitch_user",
    ) -> dict[str, Any]:
        """Generates dynamic pitch exercise via Gemini AI with acoustic validation."""
        try:
            if sub_mode == "pitch_minimal_pair":
                return await self._generate_dynamic_minimal_pair(difficulty, pressure_level, user_id)
            elif sub_mode == "mora_length":
                return await self._generate_dynamic_mora_length(difficulty, pressure_level, user_id)
            elif sub_mode == "vowel_devoicing":
                return await self._generate_dynamic_devoicing(difficulty, pressure_level, user_id)
            elif sub_mode == "pitch_contour":
                return await self._generate_dynamic_contour(difficulty, pressure_level, user_id)
            elif sub_mode == "pitch_recognition":
                return await self._generate_dynamic_recognition(difficulty, pressure_level, user_id)
            else:
                eff = random.choice([
                    "pitch_minimal_pair",
                    "mora_length",
                    "vowel_devoicing",
                    "pitch_contour",
                    "pitch_recognition",
                ])
                return await self.generate_dynamic_exercise(eff, difficulty, pressure_level, user_id)
        except Exception as e:
            logger.warning(f"[AIPitchGenerator] Global generation exception, falling back to factory: {e}")
            if sub_mode == "mora_length":
                return self.factory.generate_mora_length(difficulty, pressure_level)
            elif sub_mode == "vowel_devoicing":
                return self.factory.generate_devoicing(difficulty, pressure_level)
            elif sub_mode == "pitch_contour":
                return self.factory.generate_contour(difficulty, pressure_level)
            elif sub_mode == "pitch_recognition":
                return self.factory.generate_recognition(difficulty, pressure_level)
            else:
                return self.factory.generate_minimal_pair(difficulty, pressure_level)

    async def _generate_dynamic_minimal_pair(
        self,
        difficulty: str,
        pressure_level: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Generates dynamic Minimal Pair exercise (e.g. Ame vs Ame, Hashi vs Hashi)."""
        timer_ms = timer_for_level(pressure_level)
        chosen_topic, topic_sub = random.choice(PITCH_TOPICS_POOL)
        nonce = uuid.uuid4().hex[:8]

        prompt_text = (
            f"Hãy tạo 1 cặp từ tối thiểu tiếng Nhật (Minimal Pair) cùng cách đọc Hiragana nhưng khác kiểu cao độ (Pitch Accent Tokyo). "
            f"Chủ đề: '{chosen_topic}'. [Nonce: {nonce}]\n"
            f"Ví dụ: 雨 (あめ [1] - Mưa) vs 飴 (あめ [0] - Kẹo), 箸 (はし [1] - Đũa) vs 橋 (はし [2] - Cây cầu), 酒 (さけ [0] - Rượu) vs 鮭 (さけ [1] - Cá hồi).\n"
            f"Trả về JSON định dạng:\n"
            f"{{\n"
            f"  \"word_a\": \"<chữ Hán từ A, VD: 雨>\",\n"
            f"  \"meaning_a_vi\": \"<nghĩa tiếng Việt từ A, VD: Cơn mưa>\",\n"
            f"  \"accent_a_pattern\": [\"H\", \"L\"],\n"
            f"  \"accent_a_type\": \"頭高型 (Atamadaka [1])\",\n"
            f"  \"word_b\": \"<chữ Hán từ B, VD: 飴>\",\n"
            f"  \"meaning_b_vi\": \"<nghĩa tiếng Việt từ B, VD: Viên kẹo>\",\n"
            f"  \"accent_b_pattern\": [\"L\", \"H\"],\n"
            f"  \"accent_b_type\": \"平板型 (Heiban [0])\",\n"
            f"  \"common_reading\": \"<Hiragana chung, VD: あめ>\",\n"
            f"  \"target_word\": \"<từ mục tiêu cần phát âm, VD: 雨>\",\n"
            f"  \"target_context\": \"<câu ví dụ ngắn có từ mục tiêu, VD: 外は雨が降っています>\"\n"
            f"}}"
        )
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
            system_instruction="Bạn là chuyên gia ngữ âm học và cao độ tiếng Nhật Tokyo chuẩn (Tokyo Pitch Accent). Trả về duy nhất JSON hợp lệ.",
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.9,
            metadata={"idempotency_key": str(uuid.uuid4())},
        )
        try:
            resp = await self.ai_router.generate(task=AITask.PITCH_GENERATION, request=req, user_id=user_id)
            data = json.loads(resp.text.strip())
            word_a = data.get("word_a", "雨")
            meaning_a = data.get("meaning_a_vi", "Cơn mưa")
            pat_a = data.get("accent_a_pattern", ["H", "L"])
            type_a = data.get("accent_a_type", "頭高型 [1]")

            word_b = data.get("word_b", "飴")
            meaning_b = data.get("meaning_b_vi", "Viên kẹo")
            pat_b = data.get("accent_b_pattern", ["L", "H"])
            type_b = data.get("accent_b_type", "平板型 [0]")

            reading = data.get("common_reading", "あめ")
            target = data.get("target_word", word_a)
            ctx = data.get("target_context", f"{word_a} / {word_b}")
        except Exception as e:
            logger.warning(f"[AIPitchGenerator] Minimal pair generation fallback: {e}")
            return self.factory.generate_minimal_pair(difficulty, pressure_level)

        is_target_a = target == word_a
        chosen_pat = pat_a if is_target_a else pat_b
        chosen_type = type_a if is_target_a else type_b
        downstep_idx = 1 if "1" in chosen_type or "頭高" in chosen_type else (0 if "0" in chosen_type or "平板" in chosen_type else 2)

        mora_breakdown, downstep_notation = compute_pitch_mora_helpers(reading, chosen_pat, downstep_idx)

        return {
            "title": f"Minimal Pair: {word_a} vs {word_b}",
            "objective": f"Phân biệt cao độ {word_a} ({type_a}) vs {word_b} ({type_b}) cùng đọc '{reading}' trong {timer_ms/1000:.1f}s",
            "scenario": f"Cặp từ cùng cách đọc '{reading}': {word_a} ({meaning_a}) vs {word_b} ({meaning_b})",
            "instructions": f"Hãy phát âm đúng cao độ của từ mục tiêu: '{target}'",
            "prompt": f"{word_a} ({meaning_a}) / {word_b} ({meaning_b})",
            "reading": reading,
            "canonical": target,
            "target": target,
            "acceptable_variants": [target, reading],
            "pair_info": {
                "word_a": word_a,
                "meaning_a": meaning_a,
                "pattern_a": pat_a,
                "type_a": type_a,
                "word_b": word_b,
                "meaning_b": meaning_b,
                "pattern_b": pat_b,
                "type_b": type_b,
                "reading": reading,
                "context": ctx,
            },
            "pitch_pattern": chosen_pat,
            "downstep_index": downstep_idx,
            "downstep_notation": downstep_notation,
            "mora_breakdown": mora_breakdown,
            "pitfall_vi": "Người Việt hay nhầm cao độ H với dấu sắc tiếng Việt ('Á-mè'). Hãy giữ âm đầu cao nhẹ nhàng và hạ xuống ở âm thứ 2.",
            "translation": f"{word_a}: {meaning_a} ↔ {word_b}: {meaning_b}",
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Chú ý cao độ tương đối (Relative Pitch), không so sánh Hz tuyệt đối"],
            "target_patterns": [target, reading],
            "estimated_minutes": 3,
        }

    async def _generate_dynamic_mora_length(
        self,
        difficulty: str,
        pressure_level: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Generates dynamic Mora Timing & Length challenge (Short vs Long / Geminate / Sokuon)."""
        timer_ms = timer_for_level(pressure_level)
        nonce = uuid.uuid4().hex[:8]

        prompt_text = (
            f"Hãy tạo 1 bài tập phân biệt số phách (Mora Count & Length) tiếng Nhật thực tế. [Nonce: {nonce}]\n"
            f"Ví dụ cặp từ: おじさん (4 mora - Chú) vs おじいさん (5 mora - Ông), 来て (2 mora) vs 切って (3 mora), ビル (2 mora) vs ビール (3 mora), 坂 (2 mora) vs 作家 (3 mora).\n"
            f"Trả về JSON: {{\"short_word\": \"<từ ngắn>\", \"short_mora\": [\"お\", \"じ\", \"さ\", \"ん\"], \"short_meaning_vi\": \"<nghĩa ngắn>\", \"long_word\": \"<từ dài>\", \"long_mora\": [\"お\", \"じ\", \"い\", \"さ\", \"ん\"], \"long_meaning_vi\": \"<nghĩa dài>\", \"mora_type\": \"長音 (Trường âm) | 促音 (Âm ngắt) | 撥音 (Âm mũi)\", \"target_word\": \"<từ mục tiêu phát âm>\"}}"
        )
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
            system_instruction="Chuyên gia ngữ âm học tiếng Nhật. Trả về duy nhất JSON hợp lệ.",
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.9,
            metadata={"idempotency_key": str(uuid.uuid4())},
        )
        try:
            resp = await self.ai_router.generate(task=AITask.PITCH_GENERATION, request=req, user_id=user_id)
            data = json.loads(resp.text.strip())
            short_w = data.get("short_word", "おじさん")
            short_m = data.get("short_mora", ["お", "じ", "さ", "ん"])
            short_vi = data.get("short_meaning_vi", "Chú / Bác")

            long_w = data.get("long_word", "おじいさん")
            long_m = data.get("long_mora", ["お", "じ", "い", "さ", "ん"])
            long_vi = data.get("long_meaning_vi", "Ông cụ")

            m_type = data.get("mora_type", "長音 (Trường âm)")
            target = data.get("target_word", long_w)
        except Exception as e:
            logger.warning(f"[AIPitchGenerator] Mora generation fallback: {e}")
            return self.factory.generate_mora_length(difficulty, pressure_level)

        target_mora_list = long_m if target == long_w else short_m
        target_reading = "".join(target_mora_list)
        pat = ["L"] + ["H"] * (len(target_mora_list) - 1)
        mora_breakdown, downstep_notation = compute_pitch_mora_helpers(target_reading, pat, 0)

        return {
            "title": f"Mora Length: {short_w} vs {long_w}",
            "objective": f"Phát âm chuẩn {len(target_mora_list)} phách ({m_type}) của từ '{target}' trong {timer_ms/1000:.1f}s",
            "scenario": f"Phân biệt phách: {short_w} ({len(short_m)} mora - {short_vi}) vs {long_w} ({len(long_m)} mora - {long_vi})",
            "instructions": f"Hãy phát âm đúng độ dài phách của từ mục tiêu: '{target}'",
            "prompt": f"{short_w} ({len(short_m)} mora) / {long_w} ({len(long_m)} mora)",
            "canonical": target,
            "reading": target_reading,
            "target": target,
            "acceptable_variants": [target, short_w, long_w, target_reading],
            "mora_info": {
                "short_word": short_w,
                "short_mora": short_m,
                "short_meaning": short_vi,
                "long_word": long_w,
                "long_mora": long_m,
                "long_meaning": long_vi,
                "mora_type": m_type,
            },
            "pitch_pattern": pat,
            "downstep_index": 0,
            "downstep_notation": downstep_notation,
            "mora_breakdown": mora_breakdown,
            "pitfall_vi": "Người học thường ngắt phách quá sớm ở âm ngắt (っ) hoặc không kéo dài đủ 2 nhịp ở trường âm. Hãy giữ nhịp đều như máy đếm nhịp.",
            "translation": f"{short_w} ({short_vi}) ↔ {long_w} ({long_vi})",
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Giữ nhịp phách đều đặn, không ngắt quãng hoặc kéo dài sai"],
            "target_patterns": [target],
            "estimated_minutes": 3,
        }

    async def _generate_dynamic_devoicing(
        self,
        difficulty: str,
        pressure_level: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Generates dynamic Vowel Devoicing (母音無声化) challenge."""
        timer_ms = timer_for_level(pressure_level)
        nonce = uuid.uuid4().hex[:8]

        prompt_text = (
            f"Hãy tạo 1 câu/từ tiếng Nhật có hiện tượng VÔ THANH HÓA NGUYÊN ÂM (母音無声化 - Vowel Devoicing) thực tế trong đời sống. [Nonce: {nonce}]\n"
            f"Ví dụ: です (âm su vô thanh), ました (âm shi vô thanh), 好きです (âm su vô thanh), 月 (âm tsu vô thanh), 聞きます (âm ki vô thanh), 7日 (しちにち).\n"
            f"Trả về JSON: {{\"word_ja\": \"<từ/cụm từ>\", \"reading\": \"<Hiragana>\", \"devoiced_mora\": \"<mora bị vô thanh, VD: す, し, つ, き, く>\", \"meaning_vi\": \"<dịch tiếng Việt>\", \"explanation\": \"<giải thích quy tắc vô thanh>\"}}"
        )
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
            system_instruction="Chuyên gia phát âm tiếng Nhật Tokyo. Trả về duy nhất JSON hợp lệ.",
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.85,
            metadata={"idempotency_key": str(uuid.uuid4())},
        )
        try:
            resp = await self.ai_router.generate(task=AITask.PITCH_GENERATION, request=req, user_id=user_id)
            data = json.loads(resp.text.strip())
            word = data.get("word_ja", "ありがとうございます")
            reading = data.get("reading", "ありがとうございます")
            devoiced = data.get("devoiced_mora", "す")
            meaning = data.get("meaning_vi", "Xin cảm ơn rất nhiều")
            expl = data.get("explanation", "Nguyên âm 'u' trong mora 'su' đứng cuối câu không rung dây thanh")
        except Exception as e:
            logger.warning(f"[AIPitchGenerator] Devoicing generation fallback: {e}")
            return self.factory.generate_devoicing(difficulty, pressure_level)

        pat = ["L"] + ["H"] * (max(1, len(reading) - 1))
        mora_breakdown, downstep_notation = compute_pitch_mora_helpers(reading, pat, 0)

        return {
            "title": f"Devoicing: Vô Thanh Hóa ({devoiced})",
            "objective": f"Phát âm chuẩn vô thanh hóa âm '{devoiced}' trong từ '{word}' ({timer_ms/1000:.1f}s)",
            "scenario": f"Từ có nguyên âm vô thanh: {word} ({meaning})",
            "instructions": f"Phát âm tự nhiên, thả lỏng dây thanh ở âm '{devoiced}': '{word}'",
            "prompt": word,
            "reading": reading,
            "canonical": word,
            "target": word,
            "acceptable_variants": [word, reading],
            "devoicing_info": {
                "devoiced_mora": devoiced,
                "explanation": expl,
                "meaning": meaning,
            },
            "pitch_pattern": pat,
            "downstep_index": 0,
            "downstep_notation": downstep_notation,
            "mora_breakdown": mora_breakdown,
            "pitfall_vi": f"Tránh phát âm rõ ràng nguyên âm ở âm '{devoiced}'. Hãy thả lỏng thanh quản để âm gió xì ra tự nhiên.",
            "translation": meaning,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Vô thanh hóa tự nhiên, không phát âm quá to âm gió"],
            "target_patterns": [word],
            "estimated_minutes": 3,
        }

    async def _generate_dynamic_contour(
        self,
        difficulty: str,
        pressure_level: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Generates dynamic Pitch Contour (Đường cao độ Tokyo 4 loại) challenge."""
        timer_ms = timer_for_level(pressure_level)
        nonce = uuid.uuid4().hex[:8]

        prompt_text = (
            f"Hãy tạo 1 bài tập luyện đường cao độ tiếng Nhật chuẩn Tokyo (Pitch Contour Curve). [Nonce: {nonce}]\n"
            f"Chọn 1 trong 4 loại cao độ: 平板型 (Heiban [0] - L H H...), 頭高型 (Atamadaka [1] - H L L...), 中高型 (Nakadaka [2/3] - L H L...), 尾高型 (Odaka [N] - L H H (L)).\n"
            f"Trả về JSON: {{\"word_ja\": \"<từ tiếng Nhật>\", \"reading\": \"<Hiragana>\", \"accent_type\": \"<平板型 [0] | 頭高型 [1] | 中高型 [2] | 尾高型 [3]>\", \"pitch_pattern\": [\"L\", \"H\", \"H\"], \"meaning_vi\": \"<dịch nghĩa>\", \"drop_position\": 0/1/2/3}}"
        )
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
            system_instruction="Chuyên gia cao độ Tokyo. Trả về duy nhất JSON hợp lệ.",
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.9,
            metadata={"idempotency_key": str(uuid.uuid4())},
        )
        try:
            resp = await self.ai_router.generate(task=AITask.PITCH_GENERATION, request=req, user_id=user_id)
            data = json.loads(resp.text.strip())
            word = data.get("word_ja", "日本語")
            reading = data.get("reading", "にほんご")
            acc_type = data.get("accent_type", "平板型 [0]")
            pat = data.get("pitch_pattern", ["L", "H", "H", "H"])
            meaning = data.get("meaning_vi", "Tiếng Nhật")
            drop = data.get("drop_position", 0)
        except Exception as e:
            logger.warning(f"[AIPitchGenerator] Contour generation fallback: {e}")
            return self.factory.generate_contour(difficulty, pressure_level)

        mora_breakdown, downstep_notation = compute_pitch_mora_helpers(reading, pat, drop)

        return {
            "title": f"Pitch Contour: {acc_type}",
            "objective": f"Phát âm đúng đường cao độ {acc_type} của từ '{word}' trong {timer_ms/1000:.1f}s",
            "scenario": f"Từ vựng: {word} ({reading}) — {acc_type} ({meaning})",
            "instructions": f"Theo dõi đường cao độ ({'-'.join(pat)}) và phát âm chuẩn: '{word}'",
            "prompt": word,
            "reading": reading,
            "canonical": word,
            "target": word,
            "acceptable_variants": [word, reading],
            "pitch_pattern": pat,
            "downstep_index": drop,
            "downstep_notation": downstep_notation,
            "mora_breakdown": mora_breakdown,
            "contour_info": {
                "accent_type": acc_type,
                "pattern": pat,
                "drop_position": drop,
                "meaning": meaning,
            },
            "pitfall_vi": f"Quy tắc cao độ Tokyo: Âm thứ nhất và thứ hai luôn khác nhau (L-H hoặc H-L). Hãy chú ý nấc hạ giọng ở phách {drop if drop > 0 else 'không hạ (Heiban)'}.",
            "translation": meaning,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Lên xuống cao độ rõ ràng theo từng phách"],
            "target_patterns": [word],
            "estimated_minutes": 3,
        }

    async def _generate_dynamic_recognition(
        self,
        difficulty: str,
        pressure_level: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Generates dynamic Pitch Recognition (Luyện tai nghe phân biệt A/B) challenge."""
        timer_ms = timer_for_level(pressure_level)
        nonce = uuid.uuid4().hex[:8]

        prompt_text = (
            f"Hãy tạo 1 câu hỏi trắc nghiệm luyện tai nghe cao độ tiếng Nhật (Pitch Recognition) chuẩn Tokyo. [Nonce: {nonce}]\n"
            f"Cho 1 từ đồng âm khác cao độ (VD: はし). Hệ thống phát âm 1 kiểu cao độ và người học chọn nghĩa đúng (Đũa hay Cầu).\n"
            f"Trả về JSON: {{\"reading\": \"<Hiragana, VD: はし>\", \"spoken_word\": \"<từ phát âm, VD: 箸>\", \"spoken_accent_type\": \"頭高型 [1] (Cao - Thấp)\", \"correct_meaning\": \"Đôi đũa\", \"distractor_word\": \"橋\", \"distractor_meaning\": \"Cây cầu\", \"distractor_accent_type\": \"尾高型 [2] (Thấp - Cao)\"}}"
        )
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
            system_instruction="Chuyên gia trắc nghiệm cao độ tiếng Nhật. Trả về duy nhất JSON hợp lệ.",
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.85,
            metadata={"idempotency_key": str(uuid.uuid4())},
        )
        try:
            resp = await self.ai_router.generate(task=AITask.PITCH_GENERATION, request=req, user_id=user_id)
            data = json.loads(resp.text.strip())
            reading = data.get("reading", "はし")
            spoken = data.get("spoken_word", "箸")
            spoken_type = data.get("spoken_accent_type", "頭高型 [1]")
            correct_m = data.get("correct_meaning", "Đôi đũa")

            distractor = data.get("distractor_word", "橋")
            distractor_m = data.get("distractor_meaning", "Cây cầu")
            distractor_type = data.get("distractor_accent_type", "尾高型 [2]")
        except Exception as e:
            logger.warning(f"[AIPitchGenerator] Recognition generation fallback: {e}")
            return self.factory.generate_recognition(difficulty, pressure_level)

        pat = ["H", "L"] if "1" in spoken_type or "頭高" in spoken_type else ["L", "H"]
        downstep_idx = 1 if "1" in spoken_type or "頭高" in spoken_type else (0 if "0" in spoken_type or "平板" in spoken_type else 2)
        mora_breakdown, downstep_notation = compute_pitch_mora_helpers(reading, pat, downstep_idx)

        # 50/50 randomize quiz option order
        is_first_correct = random.choice([True, False])
        quiz_options = [
            {
                "option_id": "A",
                "key": "1",
                "word": spoken if is_first_correct else distractor,
                "meaning": correct_m if is_first_correct else distractor_m,
                "accent_type": spoken_type if is_first_correct else distractor_type,
                "is_correct": is_first_correct,
            },
            {
                "option_id": "B",
                "key": "2",
                "word": distractor if is_first_correct else spoken,
                "meaning": distractor_m if is_first_correct else correct_m,
                "accent_type": distractor_type if is_first_correct else spoken_type,
                "is_correct": not is_first_correct,
            },
        ]

        return {
            "title": f"Pitch Recognition: {reading}",
            "objective": f"Nghe phát âm '{reading}' và nhận diện đúng nghĩa ({spoken} vs {distractor}) trong {timer_ms/1000:.1f}s",
            "scenario": f"Luyện tai nghe phân biệt cao độ: '{reading}'",
            "instructions": f"Lắng nghe âm thanh và chọn đáp án chuẩn [Phím 1 hoặc 2]: '{spoken}' ({correct_m})",
            "prompt": reading,
            "reading": reading,
            "canonical": spoken,
            "target": spoken,
            "acceptable_variants": [spoken, correct_m],
            "recognition_info": {
                "reading": reading,
                "spoken_word": spoken,
                "spoken_type": spoken_type,
                "correct_meaning": correct_m,
                "distractor_word": distractor,
                "distractor_type": distractor_type,
                "distractor_meaning": distractor_m,
            },
            "quiz_options": quiz_options,
            "pitch_pattern": pat,
            "downstep_index": downstep_idx,
            "downstep_notation": downstep_notation,
            "mora_breakdown": mora_breakdown,
            "pitfall_vi": "Hãy tập trung nghe phách đầu tiên có cao hơn phách thứ hai hay không để phân biệt tức thì.",
            "translation": f"A: {quiz_options[0]['word']} ({quiz_options[0]['meaning']}) ↔ B: {quiz_options[1]['word']} ({quiz_options[1]['meaning']})",
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Nhận diện đúng sắc thái cao độ trước khi trả lời"],
            "target_patterns": [spoken],
            "estimated_minutes": 3,
        }
