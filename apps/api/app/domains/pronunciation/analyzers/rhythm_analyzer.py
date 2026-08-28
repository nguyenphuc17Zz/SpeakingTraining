from typing import Any
import numpy as np

from app.domains.pronunciation.contracts import (
    AnalysisConfidenceLevel,
    MoraUnit,
    PronunciationScoreComponent,
    RhythmAssessment,
)


class RhythmAnalyzer:
    """Analyzes speaking tempo (mora/s), pause distribution, and rhythm naturalness."""

    LEARNER_TARGET_RATE_MIN = 3.5  # mora / sec
    LEARNER_TARGET_RATE_MAX = 7.0  # mora / sec

    @classmethod
    def analyze(
        cls,
        aligned_moras: list[MoraUnit],
        total_speech_ms: int,
        pauses: list[tuple[int, int, int]],
        alignment_confidence: AnalysisConfidenceLevel,
    ) -> tuple[PronunciationScoreComponent, RhythmAssessment]:
        """Calculates speaking rate and rhythm naturalness."""
        if not aligned_moras or total_speech_ms <= 0:
            assessment = RhythmAssessment(
                overall_score=0.0,
                confidence=0.0,
                speech_rate_mora_per_sec=0.0,
                reference_rate_mora_per_sec=5.5,
                pause_count=0,
                hesitation_count=0,
                naturalness_score=0.0,
                details={},
            )
            return (
                PronunciationScoreComponent(
                    score=0.0,
                    confidence=0.0,
                    weight=0.15,
                    available=False,
                    interpretation="Needs Attention",
                ),
                assessment,
            )

        mora_count = len(aligned_moras)
        speech_sec = total_speech_ms / 1000.0
        speech_rate = round(mora_count / max(0.1, speech_sec), 1)

        # Pause classification
        hesitation_pauses = [p for p in pauses if p[2] >= 450]  # Pause > 450ms
        natural_pauses = [p for p in pauses if p[2] < 450]

        # Rate penalty
        rate_score = 95.0
        if speech_rate < cls.LEARNER_TARGET_RATE_MIN:
            # Too slow
            diff = cls.LEARNER_TARGET_RATE_MIN - speech_rate
            rate_score = max(50.0, 95.0 - diff * 15.0)
        elif speech_rate > cls.LEARNER_TARGET_RATE_MAX:
            # Too fast/rushed
            diff = speech_rate - cls.LEARNER_TARGET_RATE_MAX
            rate_score = max(60.0, 95.0 - diff * 12.0)

        # Hesitation penalty
        hesitation_penalty = min(30.0, len(hesitation_pauses) * 8.0)
        rhythm_score = round(max(40.0, rate_score - hesitation_penalty), 1)

        conf_val = 0.9 if alignment_confidence == AnalysisConfidenceLevel.HIGH else 0.6

        assessment = RhythmAssessment(
            overall_score=rhythm_score,
            confidence=conf_val,
            speech_rate_mora_per_sec=speech_rate,
            reference_rate_mora_per_sec=5.5,
            pause_count=len(pauses),
            hesitation_count=len(hesitation_pauses),
            naturalness_score=round(max(40.0, 100.0 - hesitation_penalty * 1.5), 1),
            details={
                "mora_count": mora_count,
                "speech_duration_sec": round(speech_sec, 2),
                "pauses_ms": [p[2] for p in pauses],
            },
        )

        return (
            PronunciationScoreComponent(
                score=rhythm_score,
                confidence=conf_val,
                weight=0.15,
                available=True,
                interpretation=cls._interpret(rhythm_score),
            ),
            assessment,
        )

    @staticmethod
    def _interpret(score: float) -> str:
        if score >= 90:
            return "Excellent"
        if score >= 80:
            return "Very Good"
        if score >= 70:
            return "Good"
        if score >= 60:
            return "Developing"
        return "Needs Attention"
