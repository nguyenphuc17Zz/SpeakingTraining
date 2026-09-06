"""Unit tests for Monologue CEFR/ACTFL SLA Acoustic Fluency Profiler."""

import pytest

from app.domains.monologue.analytics.pipeline import MonologuePipeline
from app.domains.monologue.analytics.rate_analyzer import SpeechRateAnalyzer
from app.domains.monologue.contracts import PauseClass, PauseContext, PauseEvent, SpeechGenre


def test_articulation_rate_isolates_pauses():
    """Articulation Rate (AR) measures pure phonation speed, isolating pauses from total elapsed time."""
    # 30 moras across 10 seconds total, but 4 seconds spent in pauses (6s phonation)
    pauses = [
        PauseEvent(start_ms=2000, end_ms=4000, duration_ms=2000, pause_class=PauseClass.LONG_PAUSE, context=PauseContext.CLAUSE_BOUNDARY),
        PauseEvent(start_ms=6000, end_ms=8000, duration_ms=2000, pause_class=PauseClass.LONG_PAUSE, context=PauseContext.SENTENCE_BOUNDARY),
    ]
    result = SpeechRateAnalyzer.analyze(
        transcript="これはテストの日本語の文です。流暢に話す練習をしています。",
        speech_duration_ms=10000,
        mora_count=30,
        pause_events=pauses,
    )

    # Speech Rate (total time): 30 moras / 10s = 3.0 moras/s
    assert result["mora_per_sec"] == 3.0

    # Articulation Rate (net phonation time 6s): 30 moras / 6s = 5.0 moras/s
    assert result["articulation_rate_mora_sec"] == 5.0

    # Phonation Time Ratio: 6s / 10s = 60.0%
    assert result["phonation_time_ratio"] == 60.0


def test_mean_length_of_run():
    """Mean Length of Run (MLR) measures the average chunk length in moras between pauses ≥ 250ms."""
    # 24 moras with 2 pauses (3 distinct fluent runs) -> 24 / 3 = 8.0 moras/run
    pauses = [
        PauseEvent(start_ms=1000, end_ms=1500, duration_ms=500, pause_class=PauseClass.NORMAL_PAUSE, context=PauseContext.CLAUSE_BOUNDARY),
        PauseEvent(start_ms=3000, end_ms=3500, duration_ms=500, pause_class=PauseClass.NORMAL_PAUSE, context=PauseContext.CLAUSE_BOUNDARY),
    ]
    result = SpeechRateAnalyzer.analyze(
        transcript="これはテストです。日本語の練習です。",
        speech_duration_ms=5000,
        mora_count=24,
        pause_events=pauses,
    )

    assert result["mean_length_of_run_mora"] == 8.0
    assert result["mean_pause_duration_ms"] == 500.0


def test_cefr_fluency_classification_benchmarks():
    """Validates classification across CEFR proficiency tiers based on Japanese SLA norms."""
    # C2 level: very fast articulation (7.5 m/s), long runs (16 m/run), high phonation (80%)
    level_c2 = SpeechRateAnalyzer.classify_cefr_fluency(
        articulation_rate=7.5,
        mean_length_of_run=16.0,
        phonation_time_ratio=80.0,
    )
    assert level_c2 == "C2"

    # B2 level: solid articulation (5.6 m/s), medium runs (9.5 m/run), steady phonation (65%)
    level_b2 = SpeechRateAnalyzer.classify_cefr_fluency(
        articulation_rate=5.6,
        mean_length_of_run=9.5,
        phonation_time_ratio=65.0,
    )
    assert level_b2 == "B2"

    # A1 level: halting articulation (2.8 m/s), fragmented runs (3.0 m/run), low phonation (35%)
    level_a1 = SpeechRateAnalyzer.classify_cefr_fluency(
        articulation_rate=2.8,
        mean_length_of_run=3.0,
        phonation_time_ratio=35.0,
    )
    assert level_a1 == "A1"


def test_short_speech_duration_handling():
    """Recordings shorter than 1000ms gracefully return None for SLA fluency metrics."""
    result = SpeechRateAnalyzer.analyze(
        transcript="はい",
        speech_duration_ms=600,
        mora_count=2,
    )
    assert result["rate_quality"] == "too_short"
    assert result["articulation_rate_mora_sec"] is None
    assert result["cefr_fluency_level"] is None


@pytest.mark.asyncio
async def test_pipeline_sla_fluency_integration():
    """Verifies that MonologuePipeline seamlessly computes and propagates SLA acoustic metrics."""
    pipeline = MonologuePipeline()
    sample_words = [
        {"word": "今日", "start_ms": 100, "end_ms": 600},
        {"word": "は", "start_ms": 650, "end_ms": 800},
        {"word": "いい", "start_ms": 1500, "end_ms": 1900},
        {"word": "天気", "start_ms": 1950, "end_ms": 2500},
        {"word": "ですね", "start_ms": 2550, "end_ms": 3200},
    ]
    metrics = await pipeline.analyze_transcript(
        transcript="今日はいい天気ですね。",
        words=sample_words,
        speech_duration_ms=4000,
        target_duration_ms=30000,
        stt_confidence=0.92,
        genre=SpeechGenre.OPINION,
        is_text_only=True,
    )

    core = metrics["speech_metrics_core"]
    assert "articulation_rate_mora_sec" in core
    assert "phonation_time_ratio" in core
    assert "mean_length_of_run_mora" in core
    assert "cefr_fluency_level" in core
    assert core["cefr_fluency_level"] in ("A1", "A2", "B1", "B2", "C1", "C2")
    assert core["phonation_time_ratio"] > 0
