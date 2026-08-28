from typing import Any

from app.domains.pronunciation.contracts import (
    AnalysisConfidenceLevel,
    AudioQualityReport,
    IntonationAssessment,
    MoraTimingAssessment,
    PhonemeAssessment,
    PitchAssessment,
    PronunciationFeedbackItem,
    PronunciationResult,
    PronunciationScoreComponent,
    ReferenceType,
    RhythmAssessment,
)
from app.domains.pronunciation.scoring.score_interpreter import ScoreInterpreter


class PronunciationScorer:
    """Computes overall pronunciation assessment by dynamically weighting available acoustic components."""

    DEFAULT_WEIGHTS = {
        "phoneme": 0.25,
        "mora": 0.25,
        "pitch": 0.20,
        "rhythm": 0.15,
        "intonation": 0.15,
    }

    @classmethod
    def calculate_overall(
        cls,
        phoneme_comp: PronunciationScoreComponent | None,
        mora_comp: PronunciationScoreComponent | None,
        pitch_comp: PronunciationScoreComponent | None,
        rhythm_comp: PronunciationScoreComponent | None,
        intonation_comp: PronunciationScoreComponent | None,
        phoneme_assessment: list[PhonemeAssessment] | None,
        mora_assessment: MoraTimingAssessment | None,
        pitch_assessment: PitchAssessment | None,
        rhythm_assessment: RhythmAssessment | None,
        intonation_assessment: IntonationAssessment | None,
        audio_quality: AudioQualityReport | None,
        top_issues: list[PronunciationFeedbackItem],
        strengths: list[str],
        practice_recommendation: str | None,
        reference_type: ReferenceType = ReferenceType.UNKNOWN,
        partial_reasons: list[str] | None = None,
    ) -> PronunciationResult:
        """
        Aggregates available component scores into overall score with confidence tracking.
        Does NOT fake 0 for missing components.
        """
        components: list[tuple[str, PronunciationScoreComponent, float]] = []

        if phoneme_comp and phoneme_comp.available:
            components.append(("phoneme", phoneme_comp, cls.DEFAULT_WEIGHTS["phoneme"]))
        if mora_comp and mora_comp.available:
            components.append(("mora", mora_comp, cls.DEFAULT_WEIGHTS["mora"]))
        if pitch_comp and pitch_comp.available:
            components.append(("pitch", pitch_comp, cls.DEFAULT_WEIGHTS["pitch"]))
        if rhythm_comp and rhythm_comp.available:
            components.append(("rhythm", rhythm_comp, cls.DEFAULT_WEIGHTS["rhythm"]))
        if intonation_comp and intonation_comp.available:
            components.append(("intonation", intonation_comp, cls.DEFAULT_WEIGHTS["intonation"]))

        reasons = list(partial_reasons or [])

        if not components:
            return PronunciationResult(
                overall_score=0.0,
                overall_confidence=AnalysisConfidenceLevel.UNCERTAIN,
                score_interpretation="Needs Attention",
                phoneme_score=phoneme_comp,
                mora_timing_score=mora_comp,
                pitch_score=pitch_comp,
                rhythm_score=rhythm_comp,
                intonation_score=intonation_comp,
                phoneme_assessment=phoneme_assessment,
                mora_assessment=mora_assessment,
                pitch_assessment=pitch_assessment,
                rhythm_assessment=rhythm_assessment,
                intonation_assessment=intonation_assessment,
                audio_quality=audio_quality,
                top_issues=top_issues,
                strengths=strengths,
                practice_recommendation=practice_recommendation,
                reference_type=reference_type,
                partial_reasons=reasons or ["No acoustic components available for scoring."],
            )

        total_weight = sum([w for _, _, w in components])
        weighted_score_sum = sum([c.score * (w / total_weight) for _, c, w in components])
        weighted_conf_sum = sum([c.confidence * (w / total_weight) for _, c, w in components])

        # Overall score
        overall_score = round(float(weighted_score_sum), 1)

        # Overall confidence level mapping
        if weighted_conf_sum >= 0.80:
            overall_conf = AnalysisConfidenceLevel.HIGH
        elif weighted_conf_sum >= 0.55:
            overall_conf = AnalysisConfidenceLevel.MEDIUM
        else:
            overall_conf = AnalysisConfidenceLevel.LOW

        interpretation = ScoreInterpreter.interpret(overall_score)

        return PronunciationResult(
            overall_score=overall_score,
            overall_confidence=overall_conf,
            score_interpretation=interpretation,
            phoneme_score=phoneme_comp,
            mora_timing_score=mora_comp,
            pitch_score=pitch_comp,
            rhythm_score=rhythm_comp,
            intonation_score=intonation_comp,
            phoneme_assessment=phoneme_assessment,
            mora_assessment=mora_assessment,
            pitch_assessment=pitch_assessment,
            rhythm_assessment=rhythm_assessment,
            intonation_assessment=intonation_assessment,
            audio_quality=audio_quality,
            top_issues=top_issues,
            strengths=strengths,
            practice_recommendation=practice_recommendation,
            engine_version="1.0.0",
            scoring_version="1.0.0",
            reference_type=reference_type,
            partial_reasons=reasons,
        )
