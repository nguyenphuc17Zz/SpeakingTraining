import pytest

from app.domains.pronunciation.analyzers.mora_timing_analyzer import MoraTimingAnalyzer
from app.domains.pronunciation.contracts import AnalysisConfidenceLevel, MoraUnit


def test_npvi_isochronous_native_timing():
    """Verify nPVI and isochrony score on smooth, isochronous Japanese mora durations."""
    durations = [120.0, 125.0, 118.0, 122.0, 120.0]
    npvi, isochrony = MoraTimingAnalyzer.calculate_npvi_isochrony(durations)

    # In perfectly uniform speech, nPVI is extremely low (< 10)
    assert npvi < 10.0
    assert isochrony > 95.0


def test_npvi_phrase_final_lengthening_compensation():
    """Verify that natural phrase-final lengthening (PFL) does not ruin isochrony score."""
    # Last mora (160ms) is naturally longer in Japanese utterance-final position
    durations = [110.0, 115.0, 112.0, 108.0, 160.0]
    npvi_comp, isochrony_comp = MoraTimingAnalyzer.calculate_npvi_isochrony(durations, compensate_pfl=True)
    npvi_raw, isochrony_raw = MoraTimingAnalyzer.calculate_npvi_isochrony(durations, compensate_pfl=False)

    # Compensated nPVI should be noticeably lower than raw
    assert npvi_comp < npvi_raw
    assert isochrony_comp >= isochrony_raw
    assert isochrony_comp > 85.0


def test_npvi_erratic_stress_timed_non_native_speech():
    """Verify erratic duration shifts trigger high nPVI and timing issue warning."""
    # Extreme non-native fluctuations: 70ms then 250ms then 60ms then 240ms
    durations = [70.0, 250.0, 60.0, 240.0, 80.0]
    npvi, isochrony = MoraTimingAnalyzer.calculate_npvi_isochrony(durations)

    assert npvi > 70.0
    assert isochrony < 60.0

    # Full analyzer flow
    moras = [
        MoraUnit(mora_index=i, kana=k, actual_duration_ms=durations[i])
        for i, k in enumerate(["こ", "ん", "に", "ち", "は"])
    ]
    comp, assessment = MoraTimingAnalyzer.analyze(
        aligned_moras=moras,
        total_speech_ms=sum(int(d) for d in durations),
        alignment_confidence=AnalysisConfidenceLevel.HIGH,
    )

    assert assessment.npvi_score is not None and assessment.npvi_score > 70.0
    assert any("nPVI" in issue for issue in assessment.top_timing_issues)
