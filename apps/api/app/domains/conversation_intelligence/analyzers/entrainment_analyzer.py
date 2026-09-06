"""Interactive Alignment & Morphosyntactic Entrainment Scorer.

Psycholinguistic Foundations:
- Pickering & Garrod (2004): Toward a mechanistic psychology of dialogue (Interactive Alignment Model).
- Reitter & Moore (2014): Alignment and task success in spoken dialogue.
- Maynard (1989) & Ide (1989): Conversational responsiveness and register discernment (Wakimae) in Japanese talk.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EntrainmentLevel(str, Enum):
    """Degrees of psycholinguistic interactive alignment."""

    RESONANT_ENGAGED = "resonant_engaged"        # High lexical & syntactic resonance (>= 80)
    MODERATE_ALIGNMENT = "moderate_alignment"    # Good conversational continuity (60 - 79)
    DISCONNECTED_ROBOTIC = "disconnected_robotic"  # Rigid, ignored cues (< 60)


@dataclass
class EntrainmentAssessment:
    """Telemetry report for interactive alignment."""

    overall_alignment_score: float
    lexical_entrainment_score: float
    register_alignment_score: float
    entrainment_level: EntrainmentLevel
    matched_lexical_primes: list[str] = field(default_factory=list)
    partner_register: str = "polite"
    user_register: str = "polite"
    feedback: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_alignment_score": round(self.overall_alignment_score, 1),
            "lexical_entrainment_score": round(self.lexical_entrainment_score, 1),
            "register_alignment_score": round(self.register_alignment_score, 1),
            "entrainment_level": self.entrainment_level.value,
            "matched_lexical_primes": self.matched_lexical_primes,
            "partner_register": self.partner_register,
            "user_register": self.user_register,
            "feedback": self.feedback,
        }


class EntrainmentAnalyzer:
    """Evaluates lexical entrainment, structural priming, and register alignment in Japanese dialogue."""

    # Japanese register markers
    POLITE_PATTERNS = [
        re.compile(r"(です|ます|でした|ました|ません|ましょう|でしょう|でしょうか|ございます)"),
    ]
    CASUAL_PATTERNS = [
        re.compile(r"(だ|だった|じゃない|だよ|だね|だよね|じゃん|わ|ぞ|ぜ|たい|ない|ちゃう|てる|よ|ね)$", re.UNICODE),
    ]

    # Shared interactional particles
    INTERACTIVE_PARTICLES = {"ね", "よ", "よね", "かな", "わ", "な"}

    @classmethod
    def detect_register(cls, text: str) -> str:
        """Determines whether utterance uses polite (丁寧) or casual (タメ口) register."""
        clean = text.strip().rstrip("。、！？!? ")
        polite_count = sum(1 for pat in cls.POLITE_PATTERNS if pat.search(clean))
        casual_count = sum(1 for pat in cls.CASUAL_PATTERNS if pat.search(clean))

        if polite_count > 0:
            return "polite"
        if casual_count > 0:
            return "casual"
        return "neutral"

    @classmethod
    def extract_content_words(cls, text: str) -> set[str]:
        """Extracts candidate content words (Kanji/Katakana words, stems) ignoring functional particles."""
        # Clean punctuation
        cleaned = re.sub(r"[。、！？!?,\.\s\(\)]", " ", text)
        # Extract Kanji compounds and Katakana loanwords (high informational salience)
        tokens = set(re.findall(r"[\u4e00-\u9faf]{2,}|[\u30a0-\u30ff]{2,}", cleaned))

        # Add common verbal/adnominal stems if >= 2 characters
        hiragana_words = set(re.findall(r"[\u3040-\u309f]{2,}", cleaned))
        functional = {
            "です", "ます", "でした", "ました", "から", "ので", "けど", "けれど",
            "たら", "れば", "こと", "もの", "よう", "そう", "これ", "それ", "あれ",
            "なん", "なに", "どう", "どこ", "どの", "いる", "ある", "する", "いう",
        }
        for hw in hiragana_words:
            if hw not in functional and len(hw) >= 2:
                tokens.add(hw)

        return tokens

    @classmethod
    def evaluate_alignment(
        cls,
        partner_turns: list[str],
        user_response: str,
        target_register: str | None = None,
    ) -> EntrainmentAssessment:
        """Calculates interactive alignment between partner's recent dialogue turns and user response.

        Args:
            partner_turns: List of partner utterances (most recent at end).
            user_response: Current user utterance.
            target_register: Explicit scenario target register ("polite", "casual") if enforced.
        """
        if not partner_turns or not user_response.strip():
            return EntrainmentAssessment(
                overall_alignment_score=75.0,
                lexical_entrainment_score=75.0,
                register_alignment_score=75.0,
                entrainment_level=EntrainmentLevel.MODERATE_ALIGNMENT,
                feedback="Lượt thoại cơ bản.",
            )

        user_content = cls.extract_content_words(user_response)
        user_reg = cls.detect_register(user_response)

        # 1. Lexical Entrainment across recent turns with exponential recency decay
        matched_primes: set[str] = set()
        weighted_overlap = 0.0
        decay = 1.0

        # Iterate from most recent partner turn backwards (up to 3 turns)
        recent_partner_turns = partner_turns[-3:][::-1]
        for i, turn in enumerate(recent_partner_turns):
            turn_words = cls.extract_content_words(turn)
            intersection = user_content.intersection(turn_words)
            matched_primes.update(intersection)

            overlap_ratio = len(intersection) / max(1, len(turn_words))
            weighted_overlap += overlap_ratio * decay
            decay *= 0.65  # Recency decay for earlier turns

        # Normalize lexical score: 0 to 100
        matched_count = len(matched_primes)
        if matched_count >= 2:
            lexical_score = 95.0
        elif matched_count == 1:
            lexical_score = 85.0
        elif len(user_content) > 0 and len(matched_primes) == 0:
            # Unrelated topic or off-topic deviation
            lexical_score = 50.0
        else:
            lexical_score = 45.0

        # 2. Register Entrainment
        partner_reg = cls.detect_register(recent_partner_turns[0]) if recent_partner_turns else "polite"
        expected_reg = target_register or partner_reg

        if user_reg == expected_reg:
            reg_score = 95.0
        elif user_reg == "neutral":
            reg_score = 80.0
        else:
            # Inappropriate register mismatch (e.g. casual in polite business conversation)
            reg_score = 50.0

        # 3. Overall Interactive Alignment Score
        overall = 0.55 * lexical_score + 0.45 * reg_score
        overall_clamped = float(max(40.0, min(98.0, overall)))

        if overall_clamped >= 80.0:
            level = EntrainmentLevel.RESONANT_ENGAGED
            feedback = "Tương tác cộng hưởng xuất sắc: Bạn lắng nghe đối phương, bắt nhịp đúng từ khóa và giữ thể ngữ đồng điệu."
        elif overall_clamped >= 60.0:
            level = EntrainmentLevel.MODERATE_ALIGNMENT
            feedback = "Mạch hội thoại tự nhiên, phản hồi phù hợp với ngữ cảnh câu hỏi."
        else:
            level = EntrainmentLevel.DISCONNECTED_ROBOTIC
            feedback = "Câu trả lời hơi rời rạc hoặc lệch thể ngữ (Register mismatch). Hãy chú ý tiếp nhận từ khóa và phong cách của đối phương."

        return EntrainmentAssessment(
            overall_alignment_score=overall_clamped,
            lexical_entrainment_score=lexical_score,
            register_alignment_score=reg_score,
            entrainment_level=level,
            matched_lexical_primes=sorted(list(matched_primes)),
            partner_register=partner_reg,
            user_register=user_reg,
            feedback=feedback,
        )
