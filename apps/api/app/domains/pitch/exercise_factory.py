"""Pitch exercise factory — small composable pools, not giant DB, provider-driven where possible."""

from __future__ import annotations

import random
from typing import Any

from app.domains.pitch.resource_provider import get_pitch_provider

# Tiny example pools (policy, not language DB) — provider is authoritative
MINIMAL_PAIRS_EXAMPLE = [
    {"a": "雨", "b": "飴", "reading": "あめ", "a_accent": "atamadaka", "b_accent": "heiban", "meaning_a": "Cơn mưa", "meaning_b": "Viên kẹo"},
    {"a": "箸", "b": "橋", "reading": "はし", "a_accent": "atamadaka", "b_accent": "odaka", "meaning_a": "Đôi đũa", "meaning_b": "Cây cầu"},
    {"a": "酒", "b": "鮭", "reading": "さけ", "a_accent": "heiban", "b_accent": "atamadaka", "meaning_a": "Rượu sake", "meaning_b": "Cá hồi"},
    {"a": "柿", "b": "牡蠣", "reading": "かき", "a_accent": "heiban", "b_accent": "atamadaka", "meaning_a": "Quả hồng", "meaning_b": "Con hàu"},
    {"a": "白", "b": "城", "reading": "しろ", "a_accent": "atamadaka", "b_accent": "heiban", "meaning_a": "Màu trắng", "meaning_b": "Lâu đài"},
    {"a": "雲", "b": "蜘蛛", "reading": "くも", "a_accent": "atamadaka", "b_accent": "heiban", "meaning_a": "Đám mây", "meaning_b": "Con nhện"},
    {"a": "今", "b": "居間", "reading": "いま", "a_accent": "atamadaka", "b_accent": "heiban", "meaning_a": "Bây giờ", "meaning_b": "Phòng khách"},
    {"a": "花", "b": "鼻", "reading": "はな", "a_accent": "odaka", "b_accent": "heiban", "meaning_a": "Bông hoa", "meaning_b": "Cái mũi"},
]

MORA_PAIRS_EXAMPLE = [
    {"short": "おじさん", "long": "おじいさん", "type": "Trường âm (長音)", "short_meaning": "Chú / Bác", "long_meaning": "Ông cụ"},
    {"short": "おばさん", "long": "おばあさん", "type": "Trường âm (長音)", "short_meaning": "Cô / Dì", "long_meaning": "Bà cụ"},
    {"short": "きて", "long": "きって", "type": "Âm ngắt (促音)", "short_meaning": "Hãy đến", "long_meaning": "Con tem"},
    {"short": "さか", "long": "さっか", "type": "Âm ngắt (促音)", "short_meaning": "Con dốc", "long_meaning": "Nhà văn"},
    {"short": "ビル", "long": "ビール", "type": "Trường âm (長音)", "short_meaning": "Tòa nhà", "long_meaning": "Bia"},
    {"short": "ゆき", "long": "ゆうき", "type": "Trường âm (長音)", "short_meaning": "Tuyết", "long_meaning": "Dũng khí"},
    {"short": "とり", "long": "とおり", "type": "Trường âm (長音)", "short_meaning": "Con chim", "long_meaning": "Con đường"},
]

DEVOICING_EXAMPLE = [
    {"word": "です", "reading": "です", "devoiced": "す", "meaning": "Là (trợ từ kết thúc)"},
    {"word": "ました", "reading": "ました", "devoiced": "し", "meaning": "Đã (quá khứ lịch sự)"},
    {"word": "すきです", "reading": "すきです", "devoiced": "す", "meaning": "Tôi thích"},
    {"word": "つき", "reading": "つき", "devoiced": "つ", "meaning": "Mặt trăng"},
    {"word": "ききます", "reading": "ききます", "devoiced": "き", "meaning": "Nghe / Hỏi"},
    {"word": "ふたつ", "reading": "ふたつ", "devoiced": "ふ", "meaning": "Hai cái"},
    {"word": "しちがつ", "reading": "しちがつ", "devoiced": "し", "meaning": "Tháng 7"},
    {"word": "くさ", "reading": "くさ", "devoiced": "く", "meaning": "Cỏ dại"},
]

CONTOUR_WORDS = [
    {"word": "日本語", "reading": "にほんご", "type": "平板型 [0]", "pattern": ["L", "H", "H", "H"], "meaning": "Tiếng Nhật"},
    {"word": "ありがとう", "reading": "ありがとう", "type": "中高型 [2]", "pattern": ["L", "H", "L", "L", "L"], "meaning": "Cảm ơn"},
    {"word": "はじめまして", "reading": "はじめまして", "type": "中高型 [4]", "pattern": ["L", "H", "H", "H", "L", "L"], "meaning": "Rất vui được gặp bạn"},
    {"word": "すし", "reading": "すし", "type": "頭高型 [1]", "pattern": ["H", "L"], "meaning": "Món sushi"},
    {"word": "ねこ", "reading": "ねこ", "type": "頭高型 [1]", "pattern": ["H", "L"], "meaning": "Con mèo"},
    {"word": "やま", "reading": "やま", "type": "尾高型 [2]", "pattern": ["L", "H"], "meaning": "Ngọn núi"},
]

TIMER_DEFAULTS = {
    "pitch_minimal_pair": 4000,
    "mora_length": 5000,
    "vowel_devoicing": 5000,
    "pitch_contour": 6000,
    "pitch_recognition": 4000,
}


class PitchExerciseFactory:
    def __init__(self):
        self.provider = get_pitch_provider()

    def _provider_pair(self) -> dict[str, Any] | None:
        # Try to query provider for same reading different accent
        # For MVP, try random minimal pair from example via provider validation
        for cand in MINIMAL_PAIRS_EXAMPLE:
            e1 = self.provider.lookup(cand["a"])
            e2 = self.provider.lookup(cand["b"])
            if e1 and e2 and e1.reading == e2.reading and e1.accent_type != e2.accent_type:
                return cand
        return random.choice(MINIMAL_PAIRS_EXAMPLE)

    def generate_minimal_pair(self, difficulty: str = "normal", pressure_level: str = "normal") -> dict[str, Any]:
        pair = self._provider_pair()
        if not pair:
            pair = random.choice(MINIMAL_PAIRS_EXAMPLE)
        a_entry = self.provider.lookup(pair["a"])
        b_entry = self.provider.lookup(pair["b"])
        return {
            "title": f"Minimal Pair: {pair['a']} vs {pair['b']}",
            "objective": f"Phân biệt {pair['a']} ({pair['a_accent']}) vs {pair['b']} ({pair['b_accent']}) cùng đọc {pair['reading']}",
            "scenario": f"Nghe {pair['a']} và {pair['b']} — cùng đọc {pair['reading']} nhưng cao độ khác nhau.",
            "instructions": "Nghe A/B, chọn đúng theo nghĩa, hoặc nói lại với cao độ đúng. Chú ý relative pitch, không phải Hz tuyệt đối.",
            "prompt": f"{pair['a']} / {pair['b']}",
            "pair": pair,
            "reading": pair["reading"],
            "a_accent": a_entry.pattern if a_entry else [],
            "b_accent": b_entry.pattern if b_entry else [],
            "canonical": pair["a"],
            "accepted": [pair["a"], pair["b"]],
            "alternatives": [],
            "resource_source": a_entry.source if a_entry else "unknown",
            "timer_limit_ms": TIMER_DEFAULTS["pitch_minimal_pair"],
            "difficulty": difficulty,
            "constraints": ["Chú ý cao độ tương đối, không so Hz tuyệt đối"],
            "target_patterns": [pair["a"], pair["b"]],
            "estimated_minutes": 4,
        }

    def generate_mora_length(self, difficulty: str = "normal", pressure_level: str = "normal") -> dict[str, Any]:
        pair = random.choice(MORA_PAIRS_EXAMPLE)
        # Try provider mora count
        prov = self.provider
        short_mora = prov.get_mora(pair["short"])
        long_mora = prov.get_mora(pair["long"])
        return {
            "title": f"Mora Length: {pair['short']} vs {pair['long']}",
            "objective": f"Phân biệt độ dài mora {pair['type']}",
            "scenario": f"Cặp từ khác số mora: {pair['short']} ({len(short_mora)} mora) vs {pair['long']} ({len(long_mora)} mora)",
            "instructions": "Nghe và nói đúng số mora, giữ timing đều, không kéo/dừng sai.",
            "prompt": f"{pair['short']} / {pair['long']}",
            "pair": pair,
            "short_mora": short_mora,
            "long_mora": long_mora,
            "canonical": pair["long"],
            "accepted": [pair["short"], pair["long"]],
            "alternatives": [],
            "timer_limit_ms": TIMER_DEFAULTS["mora_length"],
            "difficulty": difficulty,
            "constraints": ["Chuẩn hóa theo speech rate, không so ms tuyệt đối"],
            "target_patterns": [pair["short"], pair["long"]],
            "estimated_minutes": 4,
        }

    def generate_devoicing(self, difficulty: str = "normal", pressure_level: str = "normal") -> dict[str, Any]:
        word = random.choice(DEVOICING_EXAMPLE)
        entry = self.provider.lookup(word)
        return {
            "title": f"Devoicing: {word}",
            "objective": f"Luyện vô thanh hóa nguyên âm trong {word}",
            "scenario": f"Từ {word} có môi trường vô thanh hóa — nói tự nhiên.",
            "instructions": "Nói tự nhiên, không gượng ép; devoicing là xu hướng, không bắt buộc 100% silence.",
            "prompt": word,
            "canonical": word,
            "accepted": [word],
            "alternatives": [],
            "devoicing_env": True,
            "timer_limit_ms": TIMER_DEFAULTS["vowel_devoicing"],
            "difficulty": difficulty,
            "constraints": ["Tập trung vào energy/voicing, không keyword matching"],
            "target_patterns": [word],
            "estimated_minutes": 4,
        }

    def generate_contour(self, difficulty: str = "normal", pressure_level: str = "normal") -> dict[str, Any]:
        word = random.choice(CONTOUR_WORDS)
        entry = self.provider.lookup(word)
        pattern = entry.pattern if entry else ["L", "H"]
        mora = entry.mora_count if entry else 2
        return {
            "title": f"Pitch Contour: {word}",
            "objective": f"Tập đường cao độ cho {word} ({mora} mora, pattern {'-'.join(pattern)})",
            "scenario": f"Xem pattern {'-'.join(pattern)} + mora boundaries, nói theo, so sánh contour.",
            "instructions": "Giữ relative pitch, chú ý nơi hạ cao độ (downstep), không so Hz tuyệt đối.",
            "prompt": word,
            "reading": entry.reading if entry else word,
            "mora_count": mora,
            "pattern": pattern,
            "accent_type": entry.accent_type.value if entry else "unknown",
            "drop_location": entry.drop_location if entry else None,
            "canonical": word,
            "accepted": [word],
            "alternatives": [],
            "resource_source": entry.source if entry else "unknown",
            "timer_limit_ms": TIMER_DEFAULTS["pitch_contour"],
            "difficulty": difficulty,
            "constraints": ["So sánh pattern và timing ở mora level"],
            "target_patterns": [word],
            "estimated_minutes": 5,
        }

    def generate_recognition(self, difficulty: str = "normal", pressure_level: str = "normal") -> dict[str, Any]:
        pair = self._provider_pair() or random.choice(MINIMAL_PAIRS_EXAMPLE)
        # Simulate A/B audio choice
        correct = random.choice([pair["a"], pair["b"]])
        return {
            "title": f"Recognition: {pair['reading']}",
            "objective": f"Nghe và chọn đúng từ {pair['a']}/{pair['b']}",
            "scenario": f"Nghe một trong hai: {pair['a']} vs {pair['b']} (cùng đọc {pair['reading']})",
            "instructions": "Nghe A/B và chọn đáp án đúng, không cần ghi âm ở bước này.",
            "prompt": f"{pair['a']} vs {pair['b']}",
            "pair": pair,
            "correct": correct,
            "canonical": correct,
            "accepted": [correct],
            "alternatives": [pair["a"], pair["b"]],
            "timer_limit_ms": TIMER_DEFAULTS["pitch_recognition"],
            "difficulty": difficulty,
            "constraints": ["Chọn đúng cao độ"],
            "target_patterns": [correct],
            "estimated_minutes": 3,
        }

    def generate(self, sub_mode: str, **kwargs) -> dict[str, Any]:
        if sub_mode == "pitch_minimal_pair":
            return self.generate_minimal_pair(**kwargs)
        if sub_mode == "mora_length":
            return self.generate_mora_length(**kwargs)
        if sub_mode == "vowel_devoicing":
            return self.generate_devoicing(**kwargs)
        if sub_mode == "pitch_contour":
            return self.generate_contour(**kwargs)
        if sub_mode == "pitch_recognition":
            return self.generate_recognition(**kwargs)
        return self.generate_minimal_pair(**kwargs)
