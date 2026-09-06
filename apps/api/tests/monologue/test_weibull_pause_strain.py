import pytest
from app.domains.monologue.analytics.pause_analyzer import PauseAnalyzer
from app.domains.monologue.contracts import PauseClass, PauseContext, PauseEvent


def test_weibull_survival_function():
    """Verify Weibull survival probability decreases monotonically with pause duration."""
    s_short = PauseAnalyzer.weibull_survival(300)   # 300ms micro-pause
    s_medium = PauseAnalyzer.weibull_survival(750)  # 750ms median pause
    s_long = PauseAnalyzer.weibull_survival(2000)  # 2000ms long stall

    assert 0.0 < s_long < s_medium < s_short <= 1.0
    # At lambda = 750ms, S(750) = exp(-1) ≈ 0.368
    assert abs(s_medium - 0.368) < 0.02


def test_cognitive_pause_strain_grammatical_vs_hesitation():
    """Verify natural grammatical breathing produces low CPSI, while mid-phrase hesitation produces high CPSI."""
    # Natural speaker: pauses only at sentence boundaries (500ms)
    grammatical_pauses = [
        PauseEvent(start_ms=1000, end_ms=1500, duration_ms=500, pause_class=PauseClass.NORMAL_PAUSE, context=PauseContext.SENTENCE_BOUNDARY),
        PauseEvent(start_ms=3000, end_ms=3500, duration_ms=500, pause_class=PauseClass.NORMAL_PAUSE, context=PauseContext.CLAUSE_BOUNDARY),
    ]
    res_grammatical = PauseAnalyzer.compute_cognitive_strain(grammatical_pauses, speech_duration_ms=5000)

    # Struggling speaker: long hesitation pauses inside phrases and after self-repairs
    hesitation_pauses = [
        PauseEvent(start_ms=1000, end_ms=2500, duration_ms=1500, pause_class=PauseClass.LONG_PAUSE, context=PauseContext.INSIDE_PHRASE),
        PauseEvent(start_ms=3000, end_ms=5500, duration_ms=2500, pause_class=PauseClass.STALL, context=PauseContext.AFTER_SELF_REPAIR),
    ]
    res_hesitation = PauseAnalyzer.compute_cognitive_strain(hesitation_pauses, speech_duration_ms=5000)

    assert res_hesitation["cpsi"] > res_grammatical["cpsi"]
    assert res_grammatical["hazard_risk_level"] in ("low", "moderate")
    assert res_hesitation["hazard_risk_level"] == "high"
    assert res_hesitation["hesitation_pause_count"] >= 1
    assert res_grammatical["grammatical_pause_ratio"] == 1.0


def test_pause_analyzer_analyze_full_integration():
    """Verify PauseAnalyzer.analyze produces summary containing CPSI and hazard metrics."""
    words = [
        {"word": "えーと", "start_ms": 0, "end_ms": 400},
        {"word": "私は", "start_ms": 1500, "end_ms": 1800},
        {"word": "会社員", "start_ms": 3500, "end_ms": 4000},
        {"word": "です。", "start_ms": 4200, "end_ms": 4500},
    ]
    pauses, summary = PauseAnalyzer.analyze(words, speech_duration_ms=5000, transcript="えーと 私は 会社員 です。")

    assert "cognitive_pause_strain_index" in summary
    assert "grammatical_pause_ratio" in summary
    assert "hazard_risk_level" in summary
    assert summary["cognitive_pause_strain_index"] >= 0.0
