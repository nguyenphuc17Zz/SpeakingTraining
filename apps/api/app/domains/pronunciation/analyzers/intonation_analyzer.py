from typing import Any
import numpy as np

from app.domains.pronunciation.contracts import (
    AnalysisConfidenceLevel,
    IntonationAssessment,
    PitchCurve,
    PronunciationScoreComponent,
)


class IntonationAnalyzer:
    """Analyzes sentence-level intonation, sentence-final pitch rise/fall, and contour smoothness."""

    @classmethod
    def analyze(
        cls,
        target_text: str,
        pitch_curve: PitchCurve | None,
        speech_end_ms: int,
        alignment_confidence: AnalysisConfidenceLevel,
    ) -> tuple[PronunciationScoreComponent, IntonationAssessment]:
        """Assesses sentence-final intonation (question rise vs statement fall) and contour smoothness."""
        clean_text = target_text.strip()
        is_question = (
            clean_text.endswith("か")
            or clean_text.endswith("？")
            or clean_text.endswith("?")
            or clean_text.endswith("の")
        )

        expected_final = "question_rising" if is_question else "statement_falling"

        if not pitch_curve or len(pitch_curve.points) == 0 or pitch_curve.voiced_ratio < 0.15:
            assessment = IntonationAssessment(
                overall_score=0.0,
                confidence=0.0,
                sentence_final_type=expected_final,
                is_sentence_final_natural=False,
                phrase_boundaries_count=1,
                contour_smoothness=0.0,
                explanation="Dữ liệu đường cong cao độ không đủ để đánh giá ngữ điệu.",
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

        # Inspect final 300ms of voiced frames
        final_window_start = max(0, speech_end_ms - 350)
        final_points = [
            p for p in pitch_curve.points
            if p.is_voiced and p.timestamp_ms >= final_window_start
        ]

        # Calculate final slope
        if len(final_points) >= 2:
            first_semitone = final_points[0].normalized_semitones
            last_semitone = final_points[-1].normalized_semitones
            final_delta = last_semitone - first_semitone
        else:
            final_delta = 0.0

        is_rising = final_delta >= 0.8
        is_falling = final_delta <= -0.5

        if is_question:
            # Expected rising intonation
            if is_rising:
                final_score = 96.0
                is_natural = True
                explanation = "Ngữ điệu câu hỏi lên giọng cuối câu rất tự nhiên (Rising Intonation)."
            else:
                final_score = 65.0
                is_natural = False
                explanation = "Câu hỏi tiếng Nhật cần lên giọng nhẹ ở âm cuối cùng (か/の)."
        else:
            # Expected falling or neutral statement intonation
            if is_falling or abs(final_delta) < 0.8:
                final_score = 95.0
                is_natural = True
                explanation = "Ngữ điệu câu trần thuật hạ giọng tự nhiên ở cuối câu."
            else:
                final_score = 72.0
                is_natural = False
                explanation = "Cuối câu trần thuật bị lên giọng như câu hỏi (không cần thiết)."

        # Contour smoothness (variance of first differences)
        all_voiced = [p.normalized_semitones for p in pitch_curve.points if p.is_voiced]
        if len(all_voiced) >= 4:
            diffs = np.diff(all_voiced)
            smoothness_var = float(np.var(diffs))
            smoothness_score = max(50.0, 100.0 - min(40.0, smoothness_var * 15.0))
        else:
            smoothness_score = 90.0

        overall_intonation_score = round(final_score * 0.65 + smoothness_score * 0.35, 1)
        conf_val = min(
            pitch_curve.confidence,
            0.9 if alignment_confidence == AnalysisConfidenceLevel.HIGH else 0.6,
        )

        assessment = IntonationAssessment(
            overall_score=overall_intonation_score,
            confidence=conf_val,
            sentence_final_type=expected_final,
            is_sentence_final_natural=is_natural,
            phrase_boundaries_count=1,
            contour_smoothness=round(smoothness_score, 1),
            explanation=explanation,
        )

        return (
            PronunciationScoreComponent(
                score=overall_intonation_score,
                confidence=conf_val,
                weight=0.15,
                available=True,
                interpretation=cls._interpret(overall_intonation_score),
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
