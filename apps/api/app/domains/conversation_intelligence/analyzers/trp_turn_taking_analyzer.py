"""Conversational Turn-Taking & Transition Relevance Place (TRP) Projection Model.

Linguistic & Interactional Foundations:
- Sacks, Schegloff, & Jefferson (1974): A simplest systematics for the organization of turn-taking for conversation.
- Ward & Tsukahara (2000): Prosodic features which cue back-channel responses in Japanese conversation.
- Tanaka (1999): Turn-Taking in Japanese Talk-in-Interaction (grammar, prosody, and collaborative overlap).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TurnTransitionType(str, Enum):
    """Categorization of turn transitions in interaction."""

    NATIVE_OPTIMAL = "native_optimal"              # 50ms - 600ms at TRP
    COLLABORATIVE_OVERLAP = "collaborative_overlap"  # -200ms - 0ms at valid TRP
    UNWARRANTED_INTERRUPTION = "unwarranted_interruption"  # < -200ms or breaking incomplete clause
    MILD_PAUSE = "mild_pause"                      # 600ms - 1200ms
    AWKWARD_DEAD_SILENCE = "awkward_dead_silence"  # > 1200ms
    STANDALONE_AIZUCHI = "standalone_aizuchi"      # Reactive backchannel


@dataclass
class TRPAssessment:
    """Telemetry report for conversational turn transition."""

    latency_ms: int
    transition_type: TurnTransitionType
    syntactic_trp_prob: float
    prosodic_trp_prob: float | None
    composite_trp_prob: float
    turn_timing_score: float
    feedback: str
    is_valid_turn_exchange: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "latency_ms": self.latency_ms,
            "transition_type": self.transition_type.value,
            "syntactic_trp_prob": round(self.syntactic_trp_prob, 2),
            "prosodic_trp_prob": round(self.prosodic_trp_prob, 2) if self.prosodic_trp_prob is not None else None,
            "composite_trp_prob": round(self.composite_trp_prob, 2),
            "turn_timing_score": round(self.turn_timing_score, 1),
            "feedback": self.feedback,
            "is_valid_turn_exchange": self.is_valid_turn_exchange,
        }


class TRPTurnTakingAnalyzer:
    """Evaluates transition relevance places and inter-turn latency timing in Japanese dialogues."""

    # Syntactic clause-final and sentence-final TRP markers in Japanese
    SYNTACTIC_TRP_PATTERNS = [
        # Polite sentence endings + particles
        re.compile(r"(です|ます|でした|ました|でしたら|ません|ましょう)(ね|よ|よね|か|の)?$", re.UNICODE),
        # Casual sentence endings
        re.compile(r"(だ|だった|じゃない|だよ|だね|だよね|じゃん|よ|ね|よね|の|わ|ぞ|ぜ)$", re.UNICODE),
        # Conjunctive clause boundaries projecting completion or handoff
        re.compile(r"(から|ので|けど|けれど|たら|ば|なら|と|し|て|で|のに)$", re.UNICODE),
        # Trailing-off conversational completions (Tanaka 1999)
        re.compile(r"(んだけど|ですけど|からさ|のでさ|って思って|っていうか)[\.…]*$", re.UNICODE),
        # Questions
        re.compile(r"(\?|？|でしょうか|ですか|のかな)$", re.UNICODE),
    ]

    # Incomplete syntactic boundaries (dangerous to interrupt)
    INCOMPLETE_BOUNDARY_PATTERNS = [
        re.compile(r"(を|に|が|へ|で|と|の|は)$", re.UNICODE),  # Hanging particles
        re.compile(r"(お|ご)[a-zA-Zぁ-んァ-ヶ一-龥]+$", re.UNICODE),  # Prefix mid-word
    ]

    @classmethod
    def evaluate_syntactic_trp(cls, partner_utterance: str) -> float:
        """Calculates probability [0.0, 1.0] that partner's utterance has reached a syntactic TRP."""
        clean = partner_utterance.strip().rstrip("。、 \t")
        if not clean:
            return 1.0

        # Check incomplete patterns first
        for pat in cls.INCOMPLETE_BOUNDARY_PATTERNS:
            if pat.search(clean):
                return 0.25

        # Check full TRP patterns
        for pat in cls.SYNTACTIC_TRP_PATTERNS:
            if pat.search(clean):
                return 0.92

        # General terminal punctuation
        if partner_utterance.strip().endswith(("。", "！", "？", ".", "!", "?")):
            return 0.88

        # Default moderate probability for complete sentences without explicit particle
        return 0.60

    @classmethod
    def evaluate_turn_transition(
        cls,
        partner_utterance: str,
        user_utterance: str,
        latency_ms: int,
        prosodic_boundary_fall_or_rise: bool | None = None,
        is_aizuchi: bool = False,
    ) -> TRPAssessment:
        """Evaluates conversational turn transition dynamics and inter-turn latency timing.

        Args:
            partner_utterance: Text of the previous speaker's turn.
            user_utterance: Text of the user's incoming response.
            latency_ms: Milliseconds between partner speech end and user speech start.
                Negative value means user started before partner ended (overlap/interruption).
            prosodic_boundary_fall_or_rise: Whether pitch showed terminal rise/fall cue.
            is_aizuchi: Whether user utterance is a backchannel (相槌).
        """
        syn_prob = cls.evaluate_syntactic_trp(partner_utterance)

        # Composite TRP probability
        if prosodic_boundary_fall_or_rise is not None:
            pro_prob = 0.90 if prosodic_boundary_fall_or_rise else 0.40
            composite_trp = 0.60 * syn_prob + 0.40 * pro_prob
        else:
            pro_prob = None
            composite_trp = syn_prob

        # Case 1: Standalone Aizuchi
        if is_aizuchi:
            trans_type = TurnTransitionType.STANDALONE_AIZUCHI
            score = 95.0 if -100 <= latency_ms <= 800 else 80.0
            feedback = "Tung hứng 相槌 (Aizuchi) đúng nhịp, duy trì kết nối tự nhiên với đối phương."
            return TRPAssessment(
                latency_ms=latency_ms,
                transition_type=trans_type,
                syntactic_trp_prob=syn_prob,
                prosodic_trp_prob=pro_prob,
                composite_trp_prob=composite_trp,
                turn_timing_score=score,
                feedback=feedback,
                is_valid_turn_exchange=True,
            )

        # Case 2: Interruption vs Collaborative Overlap
        if latency_ms < 0:
            if latency_ms >= -200 and composite_trp >= 0.70:
                trans_type = TurnTransitionType.COLLABORATIVE_OVERLAP
                score = 90.0
                feedback = "Gối đầu lượt thoại tự nhiên (Collaborative Overlap) khi câu của đối phương đã rõ ý."
                valid = True
            else:
                trans_type = TurnTransitionType.UNWARRANTED_INTERRUPTION
                overlap_penalty = min(50.0, abs(latency_ms) * 0.1)
                trp_penalty = (1.0 - composite_trp) * 30.0
                score = max(30.0, 85.0 - overlap_penalty - trp_penalty)
                feedback = "Cướp lời khi đối phương chưa dứt ý hoặc chưa đến điểm chuyển giao lượt thoại (TRP)."
                valid = False
            return TRPAssessment(
                latency_ms=latency_ms,
                transition_type=trans_type,
                syntactic_trp_prob=syn_prob,
                prosodic_trp_prob=pro_prob,
                composite_trp_prob=composite_trp,
                turn_timing_score=round(score, 1),
                feedback=feedback,
                is_valid_turn_exchange=valid,
            )

        # Case 3: Positive Latency (User starts after partner ends)
        if 50 <= latency_ms <= 600:
            trans_type = TurnTransitionType.NATIVE_OPTIMAL
            score = 96.0
            feedback = "Thời gian phản xạ tiếp lời hoàn hảo (Native Turn Latency 150-500ms)."
            valid = True
        elif 600 < latency_ms <= 1200:
            trans_type = TurnTransitionType.MILD_PAUSE
            diff = latency_ms - 600
            score = max(70.0, 95.0 - diff * 0.04)
            feedback = "Tiếp lời hơi chậm nhẹ nhưng vẫn trong ngưỡng trò chuyện chấp nhận được."
            valid = True
        elif latency_ms > 1200:
            trans_type = TurnTransitionType.AWKWARD_DEAD_SILENCE
            diff = latency_ms - 1200
            score = max(40.0, 70.0 - diff * 0.03)
            feedback = "Khoảng dừng chết quá dài (>1.2s) tạo cảm giác ngượng ngùng trong giao tiếp tiếng Nhật."
            valid = True
        else:
            # Very fast transition 0 - 50ms
            trans_type = TurnTransitionType.NATIVE_OPTIMAL
            score = 92.0
            feedback = "Bắt nhịp tiếp lời tức thì, phản xạ nhanh nhạy."
            valid = True

        return TRPAssessment(
            latency_ms=latency_ms,
            transition_type=trans_type,
            syntactic_trp_prob=syn_prob,
            prosodic_trp_prob=pro_prob,
            composite_trp_prob=composite_trp,
            turn_timing_score=round(score, 1),
            feedback=feedback,
            is_valid_turn_exchange=valid,
        )
