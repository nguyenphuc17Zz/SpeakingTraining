import numpy as np

from app.domains.pronunciation.contracts import (
    AnalysisConfidenceLevel,
    MoraTimingAssessment,
    MoraUnit,
    PronunciationScoreComponent,
)


class MoraTimingAnalyzer:
    """Analyzes Japanese mora durations, isochrony, long vowel extensions, and Sokuon timing."""

    @classmethod
    def analyze(
        cls,
        aligned_moras: list[MoraUnit],
        total_speech_ms: int,
        alignment_confidence: AnalysisConfidenceLevel,
    ) -> tuple[PronunciationScoreComponent, MoraTimingAssessment]:
        """Calculates mora timing scores and flags timing abnormalities."""
        if not aligned_moras or total_speech_ms <= 0:
            assessment = MoraTimingAssessment(
                overall_score=0.0,
                confidence=0.0,
                mora_units=[],
                speech_rate_mora_per_sec=0.0,
                rhythm_regularity_score=0.0,
                top_timing_issues=[],
            )
            return (
                PronunciationScoreComponent(
                    score=0.0,
                    confidence=0.0,
                    weight=0.25,
                    available=False,
                    interpretation="Needs Attention",
                ),
                assessment,
            )

        mora_count = len(aligned_moras)
        speech_sec = total_speech_ms / 1000.0
        speech_rate = round(mora_count / max(0.1, speech_sec), 1)

        durations = [float(m.actual_duration_ms or 100) for m in aligned_moras]
        avg_mora_dur = float(np.mean(durations))

        assessed_moras: list[MoraUnit] = []
        timing_issues: list[str] = []
        mora_scores: list[float] = []

        for m in aligned_moras:
            actual_dur = float(m.actual_duration_ms or avg_mora_dur)
            ratio_to_avg = actual_dur / max(1.0, avg_mora_dur)
            m_score = 95.0
            issue = None

            # 1. Sokuon (っ) timing
            if m.kana == "っ":
                if ratio_to_avg < 0.65:
                    issue = "Âm ngắt「っ」bị quá ngắn hoặc bị lướt qua."
                    timing_issues.append(f"Mora {m.mora_index+1} (っ): Thời lượng âm ngắt quá ngắn")
                    m_score = 62.0
                elif ratio_to_avg > 1.70:
                    issue = "Khoảng dừng âm ngắt「っ」bị kéo dài quá lâu."
                    m_score = 75.0
                else:
                    m_score = 95.0

            # 2. Long Vowel (ー / vowel prolongation)
            elif m.is_special and m.special_type == "long_vowel":
                if ratio_to_avg < 0.70:
                    issue = "Trường âm bị phát âm quá ngắn (chưa đủ 2 mora)."
                    timing_issues.append(f"Mora {m.mora_index+1} ({m.kana}): Trường âm bị ngắn")
                    m_score = 65.0
                elif ratio_to_avg > 1.80:
                    issue = "Trường âm bị ngân quá dài."
                    m_score = 78.0
                else:
                    m_score = 96.0

            # 3. Hatsuon (ん)
            elif m.kana == "ん":
                if ratio_to_avg < 0.55:
                    issue = "Âm「ん」bị nuốt âm hoặc quá ngắn."
                    timing_issues.append(f"Mora {m.mora_index+1} (ん): Âm mũi 'n' bị ngắn")
                    m_score = 70.0
                else:
                    m_score = 95.0

            # 4. Standard mora timing
            else:
                if ratio_to_avg < 0.40:
                    issue = f"Mora「{m.kana}」bị nuốt âm."
                    m_score = 70.0
                elif ratio_to_avg > 2.20:
                    issue = f"Mora「{m.kana}」bị kéo dài bất thường."
                    m_score = 75.0
                else:
                    m_score = 95.0

            mora_scores.append(m_score)
            assessed_moras.append(
                MoraUnit(
                    mora_index=m.mora_index,
                    kana=m.kana,
                    phonemes=m.phonemes,
                    is_special=m.is_special,
                    special_type=m.special_type,
                    expected_duration_ms=m.expected_duration_ms,
                    actual_duration_ms=m.actual_duration_ms,
                    duration_ratio=round(ratio_to_avg, 2),
                    score=m_score,
                    issue=issue,
                    confidence=m.confidence,
                )
            )

        # Compute SOTA Normalized Pairwise Variability Index (nPVI) Mora Isochrony
        npvi_val, isochrony_score = cls.calculate_npvi_isochrony(durations, compensate_pfl=True)
        if npvi_val > 65.0:
            timing_issues.append("Nhịp điệu mora thiếu đều đặn (nPVI cao: các mora chênh lệch thời lượng quá mức)")

        regularity_penalty = max(0.0, (100.0 - isochrony_score) * 0.25)
        overall_mora_score = round(max(30.0, float(np.mean(mora_scores)) - regularity_penalty), 1)

        conf_val = 0.9 if alignment_confidence == AnalysisConfidenceLevel.HIGH else (0.65 if alignment_confidence == AnalysisConfidenceLevel.MEDIUM else 0.4)

        assessment = MoraTimingAssessment(
            overall_score=overall_mora_score,
            confidence=conf_val,
            mora_units=assessed_moras,
            speech_rate_mora_per_sec=speech_rate,
            rhythm_regularity_score=isochrony_score,
            top_timing_issues=timing_issues[:3],
            npvi_score=npvi_val,
            isochrony_score=isochrony_score,
        )

        return (
            PronunciationScoreComponent(
                score=overall_mora_score,
                confidence=conf_val,
                weight=0.25,
                available=True,
                interpretation=cls._interpret(overall_mora_score),
            ),
            assessment,
        )

    @classmethod
    def calculate_npvi_isochrony(
        cls,
        durations: list[float],
        compensate_pfl: bool = True,
    ) -> tuple[float, float]:
        """Calculates Normalized Pairwise Variability Index (nPVI) and Isochrony Score.

        Formula:
            nPVI = (100 / (m - 1)) * sum(|(d_k - d_{k+1}) / ((d_k + d_{k+1}) / 2)|)

        Phonetic Grounding:
            - Grabe & Low (2002); Ling et al. (2000).
            - Native Japanese mora-timed speech exhibits low nPVI (35 - 48).
            - Non-native stress-timed interference produces elevated nPVI (> 65).
            - Optional Phrase-Final Lengthening (PFL) compensation prevents unfair penalty on utterance ends.
        """
        import math

        m = len(durations)
        if m < 2:
            return 0.0, 100.0

        diffs = []
        for k in range(m - 1):
            d1 = durations[k]
            d2 = durations[k + 1]
            avg = (d1 + d2) / 2.0
            if avg > 0:
                diffs.append(abs(d1 - d2) / avg)

        raw_npvi = float((100.0 / len(diffs)) * sum(diffs))

        if compensate_pfl and m >= 3:
            # Core nPVI excluding the phrase-final elongation
            core_diffs = diffs[:-1]
            core_npvi = float((100.0 / len(core_diffs)) * sum(core_diffs))
            effective_npvi = 0.85 * core_npvi + 0.15 * raw_npvi
        else:
            effective_npvi = raw_npvi

        # Isochrony Score: Gaussian curve centered at optimal ~38.0
        dev = max(0.0, effective_npvi - 38.0)
        isochrony = 100.0 * math.exp(-(dev**2) / (2.0 * (20.0**2)))
        isochrony_score = round(float(np.clip(isochrony, 20.0, 100.0)), 1)

        return round(effective_npvi, 1), isochrony_score

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
