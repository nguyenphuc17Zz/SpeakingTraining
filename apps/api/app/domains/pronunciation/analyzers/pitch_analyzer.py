from typing import Any
import numpy as np

from app.domains.pronunciation.contracts import (
    AnalysisConfidenceLevel,
    MoraUnit,
    PitchAccentPattern,
    PitchAssessment,
    PitchCurve,
    PronunciationScoreComponent,
)
from app.domains.pronunciation.japanese.pitch_accent_resolver import PitchAccentTargetResolver


class PitchAnalyzerComponent:
    """Analyzes Japanese pitch accent patterns (Heiban, Atamadaka, Nakadaka, Odaka) and pitch contour alignment."""

    @classmethod
    def analyze(
        cls,
        target_text: str,
        pitch_curve: PitchCurve | None,
        aligned_moras: list[MoraUnit],
        speech_start_ms: int,
        alignment_confidence: AnalysisConfidenceLevel,
    ) -> tuple[PronunciationScoreComponent, PitchAssessment]:
        """Compares speaker pitch curve with expected Tokyo Japanese Pitch Accent pattern."""
        # Resolve lexical target accent
        target_pattern, target_kernel, expected_levels = PitchAccentTargetResolver.resolve_target(target_text)

        if not pitch_curve or len(pitch_curve.points) == 0 or pitch_curve.voiced_ratio < 0.15:
            assessment = PitchAssessment(
                overall_score=0.0,
                confidence=0.0,
                accent_pattern_target=target_pattern,
                accent_pattern_observed=PitchAccentPattern.UNKNOWN,
                pattern_matched=False,
                pitch_curve=pitch_curve,
                reference_pitch_curve=None,
                explanation="Không đủ dữ liệu thanh điệu rõ ràng để đánh giá cao độ.",
            )
            return (
                PronunciationScoreComponent(
                    score=0.0,
                    confidence=0.0,
                    weight=0.20,
                    available=False,
                    interpretation="Needs Attention",
                ),
                assessment,
            )

        # Map pitch points to each mora based on duration bounds
        mora_pitches: list[list[float]] = []
        curr_m_start = speech_start_ms

        for m in aligned_moras:
            m_dur = m.actual_duration_ms or 120
            m_end = curr_m_start + m_dur

            pts_in_mora = [
                p.normalized_semitones
                for p in pitch_curve.points
                if p.is_voiced and curr_m_start <= p.timestamp_ms <= m_end
            ]
            mora_pitches.append(pts_in_mora)
            curr_m_start = m_end

        # Calculate average pitch (semitones) per mora
        mora_avg_pitches = [
            float(np.mean(pts)) if len(pts) > 0 else 0.0 for pts in mora_pitches
        ]

        # Determine observed pattern
        observed_pattern, observed_levels = cls._classify_observed_pattern(mora_avg_pitches)

        # Calculate pitch score based on pattern match
        pattern_matched = (observed_pattern == target_pattern)
        mora_match_count = sum(
            1 for o, e in zip(observed_levels, expected_levels) if o == e
        )
        level_match_ratio = mora_match_count / float(max(1, len(expected_levels)))

        if pattern_matched:
            pitch_score = round(85.0 + 15.0 * level_match_ratio, 1)
            explanation = f"Mô hình cao độ phù hợp với quy tắc Tokyo ({target_pattern.value})."
        else:
            pitch_score = round(55.0 + 30.0 * level_match_ratio, 1)
            explanation = (
                f"Cao độ thực tế ({observed_pattern.value}) khác với mô hình mục tiêu ({target_pattern.value})."
            )

        conf_val = min(
            pitch_curve.confidence,
            0.9 if alignment_confidence == AnalysisConfidenceLevel.HIGH else 0.6,
        )

        assessment = PitchAssessment(
            overall_score=pitch_score,
            confidence=conf_val,
            accent_pattern_target=target_pattern,
            accent_pattern_observed=observed_pattern,
            pattern_matched=pattern_matched,
            pitch_curve=pitch_curve,
            reference_pitch_curve=None,
            explanation=explanation,
        )

        return (
            PronunciationScoreComponent(
                score=pitch_score,
                confidence=conf_val,
                weight=0.20,
                available=True,
                interpretation=cls._interpret(pitch_score),
            ),
            assessment,
        )

    @classmethod
    def _classify_observed_pattern(
        cls, mora_avg_pitches: list[float]
    ) -> tuple[PitchAccentPattern, list[str]]:
        """Classifies observed relative semitone contours into High / Low sequence and pattern."""
        if not mora_avg_pitches:
            return PitchAccentPattern.UNKNOWN, []

        if len(mora_avg_pitches) == 1:
            return PitchAccentPattern.HEIBAN, ["H" if mora_avg_pitches[0] >= 0.0 else "L"]

        # Tokyo Dialect core rule: Mora 1 vs Mora 2
        # If Mora 1 is significantly higher than Mora 2 (>= +1.2 semitones diff) -> Atamadaka
        m1 = mora_avg_pitches[0]
        m2 = mora_avg_pitches[1]

        levels = []
        # Relative threshold
        mean_pitch = float(np.mean(mora_avg_pitches))
        for p in mora_avg_pitches:
            levels.append("H" if p >= mean_pitch - 0.2 else "L")

        if m1 - m2 >= 1.2:
            return PitchAccentPattern.ATAMADAKA, levels

        # If it rises at Mora 2 and stays high -> Heiban
        # If it falls at later moras -> Nakadaka
        if len(mora_avg_pitches) >= 3:
            later_pitches = mora_avg_pitches[2:]
            if any(lp < m2 - 1.5 for lp in later_pitches):
                return PitchAccentPattern.NAKADAKA, levels

        return PitchAccentPattern.HEIBAN, levels

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
