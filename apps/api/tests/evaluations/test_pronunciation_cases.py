import pytest
from app.domains.pronunciation.analyzers.mora_timing_analyzer import MoraTimingAnalyzer
from app.domains.pronunciation.analyzers.phoneme_analyzer import PhonemeAnalyzer
from app.domains.pronunciation.analyzers.pitch_analyzer import PitchAnalyzerComponent
from app.domains.pronunciation.contracts import (
    AnalysisConfidenceLevel,
    MoraUnit,
    PitchAccentPattern,
    PitchCurve,
    PitchPoint,
    PronunciationAnalysisPolicy,
    PronunciationResult,
    PronunciationTarget,
    ReferenceType,
    TargetType,
)
from app.domains.pronunciation.japanese.issue_taxonomy import JapaneseIssueType
from app.domains.pronunciation.japanese.mora_analyzer import JapaneseMoraAnalyzer
from app.domains.pronunciation.japanese.pitch_accent_resolver import PitchAccentTargetResolver
from app.domains.pronunciation.learning_signal_extractor import PronunciationLearningSignalExtractor
from app.domains.pronunciation.pipeline import PronunciationPipeline
from tests.unit.test_pronunciation_pipeline import create_synthetic_wav


@pytest.mark.asyncio
async def test_case_a_normal_japanese_sentence():
    """Case A — Full normal sentence: きょうは映画を見ました。"""
    wav_bytes = create_synthetic_wav(duration_sec=2.2, freq_hz=210.0, amplitude=0.4)
    target = PronunciationTarget(
        reference_text="きょうは映画を見ました。",
        expected_reading="きょうはえいがをみました",
        target_type=TargetType.SENTENCE,
    )

    result = await PronunciationPipeline.run(
        audio_bytes=wav_bytes,
        target=target,
        user_transcript="きょうは映画を見ました",
    )

    assert result.overall_score >= 60.0
    assert result.overall_confidence in [AnalysisConfidenceLevel.HIGH, AnalysisConfidenceLevel.MEDIUM]
    assert result.mora_assessment is not None
    assert len(result.mora_assessment.mora_units) >= 10


def test_case_b_long_vowel_distinction():
    """Case B — Long vowel: おばさん (4 morae) vs おばあさん (5 morae)."""
    m_short = JapaneseMoraAnalyzer.segment_moras("おばさん")
    m_long = JapaneseMoraAnalyzer.segment_moras("おばあさん")

    assert len(m_short) == 4
    assert len(m_long) == 5

    # Simulate user saying short vowel when long vowel is expected (obasan instead of obaasan)
    # Long vowel mora has very short duration
    short_aligned = [
        MoraUnit(mora_index=0, kana="お", phonemes=["o"], expected_duration_ms=150, actual_duration_ms=140),
        MoraUnit(mora_index=1, kana="ば", phonemes=["b", "a"], expected_duration_ms=150, actual_duration_ms=140),
        MoraUnit(mora_index=2, kana="あ", phonemes=[":"], is_special=True, special_type="long_vowel", expected_duration_ms=150, actual_duration_ms=40),  # Much too short
        MoraUnit(mora_index=3, kana="さ", phonemes=["s", "a"], expected_duration_ms=150, actual_duration_ms=140),
        MoraUnit(mora_index=4, kana="ん", phonemes=["N"], is_special=True, special_type="nasal", expected_duration_ms=150, actual_duration_ms=140),
    ]

    _, mora_assessment = MoraTimingAnalyzer.analyze(
        aligned_moras=short_aligned,
        total_speech_ms=600,
        alignment_confidence=AnalysisConfidenceLevel.HIGH,
    )

    assert any("Trường âm" in issue for issue in mora_assessment.top_timing_issues)


def test_case_c_sokuon_small_tsu_distinction():
    """Case C — Small っ: きて (2 morae) vs きって (3 morae)."""
    m_kitte = JapaneseMoraAnalyzer.segment_moras("きって")
    assert len(m_kitte) == 3

    # If sokuon pause is rushed (< 0.6x avg duration)
    rushed_sokuon = [
        MoraUnit(mora_index=0, kana="き", phonemes=["k", "i"], expected_duration_ms=160, actual_duration_ms=150),
        MoraUnit(mora_index=1, kana="っ", phonemes=["Q"], is_special=True, special_type="gemination", expected_duration_ms=160, actual_duration_ms=30),  # Skipped pause
        MoraUnit(mora_index=2, kana="て", phonemes=["t", "e"], expected_duration_ms=160, actual_duration_ms=150),
    ]

    _, mora_assessment = MoraTimingAnalyzer.analyze(
        aligned_moras=rushed_sokuon,
        total_speech_ms=330,
        alignment_confidence=AnalysisConfidenceLevel.HIGH,
    )

    assert any("っ" in issue for issue in mora_assessment.top_timing_issues)


def test_case_d_hatsuon_shinbun():
    """Case D — Hatsuon: しんぶん (4 morae)."""
    moras = JapaneseMoraAnalyzer.segment_moras("しんぶん")
    assert len(moras) == 4
    assert moras[1].kana == "ん"
    assert moras[3].kana == "ん"


def test_case_e_pitch_accent_matching():
    """Case E — Pitch Accent pattern identification."""
    pat, kernel, levels = PitchAccentTargetResolver.resolve_target("あめ")
    assert pat == PitchAccentPattern.ATAMADAKA
    assert levels == ["H", "L"]

    # Pitch curve matching Atamadaka (Mora 1 High, Mora 2 Low)
    aligned_moras = [
        MoraUnit(mora_index=0, kana="あ", expected_duration_ms=200, actual_duration_ms=200),
        MoraUnit(mora_index=1, kana="め", expected_duration_ms=200, actual_duration_ms=200),
    ]
    points = [
        PitchPoint(timestamp_ms=50, frequency_hz=250.0, normalized_semitones=2.5, is_voiced=True),
        PitchPoint(timestamp_ms=150, frequency_hz=250.0, normalized_semitones=2.2, is_voiced=True),
        PitchPoint(timestamp_ms=250, frequency_hz=180.0, normalized_semitones=-2.0, is_voiced=True),
        PitchPoint(timestamp_ms=350, frequency_hz=180.0, normalized_semitones=-2.1, is_voiced=True),
    ]
    curve = PitchCurve(points=points, voiced_ratio=0.9, confidence=0.9)

    score_comp, pitch_assessment = PitchAnalyzerComponent.analyze(
        target_text="あめ",
        pitch_curve=curve,
        aligned_moras=aligned_moras,
        speech_start_ms=0,
        alignment_confidence=AnalysisConfidenceLevel.HIGH,
    )

    assert pitch_assessment.pattern_matched is True
    assert pitch_assessment.accent_pattern_observed == PitchAccentPattern.ATAMADAKA
    assert score_comp.score >= 85.0


@pytest.mark.asyncio
async def test_case_f_noisy_recording_confidence_graceful_handling():
    """Case F — Low quality audio should yield low confidence / graceful handling without crashing."""
    empty_or_bad_wav = create_synthetic_wav(duration_sec=0.1, freq_hz=0.0, amplitude=0.001)
    target = PronunciationTarget(
        reference_text="こんにちは",
        expected_reading="こんにちは",
        target_type=TargetType.WORD,
    )

    result = await PronunciationPipeline.run(
        audio_bytes=empty_or_bad_wav,
        target=target,
    )

    assert result.overall_confidence in [AnalysisConfidenceLevel.LOW, AnalysisConfidenceLevel.UNCERTAIN]
    assert result.audio_quality is not None
    assert result.audio_quality.is_usable is False
    assert len(result.partial_reasons) > 0


@pytest.mark.asyncio
async def test_case_g_full_gakkou_practice_and_learning_signal_extraction():
    """Scenario 110 verification: User practices がっこう -> gets scores, top issues, learning signals."""
    wav_bytes = create_synthetic_wav(duration_sec=1.5, freq_hz=220.0, amplitude=0.4)
    target = PronunciationTarget(
        reference_text="学校",
        expected_reading="がっこう",
        target_type=TargetType.WORD,
    )

    result = await PronunciationPipeline.run(
        audio_bytes=wav_bytes,
        target=target,
        user_transcript="がっこう",
    )

    # Assert subscore presence
    assert result.phoneme_score is not None
    assert result.mora_timing_score is not None
    assert result.pitch_score is not None
    assert result.rhythm_score is not None
    assert result.intonation_score is not None

    # Test Learning Signal Extractor converts result to Phase 5 memory candidates
    signals = PronunciationLearningSignalExtractor.extract_from_pronunciation_result(
        result=result,
        user_id="user_test_123",
        session_id="session_test_456",
    )
    assert isinstance(signals, list)
