import pytest
from app.domains.monologue.analytics.self_repair_analyzer import SelfRepairAnalyzer


def test_levelt_tripartite_repair_detection():
    """Verify Levelt tripartite alignment captures Reparandum, Interregnum, and Reparans."""
    analyzer = SelfRepairAnalyzer()

    # Utterance with explicit editing cue and repair
    transcript = "昨日は日本で働く……正確に言うと、日本のIT会社で働くことです。"
    events, summary = analyzer.analyze(transcript)

    assert summary["repair_count"] >= 1
    assert summary["success_count"] >= 1
    assert summary["repair_efficiency_ratio"] >= 0.8
    assert summary["monitoring_quality"] == "active_monitoring"


def test_levelt_word_level_conjugation_repair():
    """Verify word-level stem comparison detects instantaneous self-correction."""
    analyzer = SelfRepairAnalyzer()

    words = [
        {"word": "明日", "start_ms": 0, "end_ms": 300},
        {"word": "京都に", "start_ms": 400, "end_ms": 700},
        {"word": "行きます", "start_ms": 800, "end_ms": 1100},
        {"word": "行きました", "start_ms": 1400, "end_ms": 1800},  # immediate correction of verb form
    ]

    events, summary = analyzer.analyze("明日京都に行きます 行きました", words=words)

    assert summary["repair_count"] >= 1
    assert any("行きます -> 行きました" in e.fragment for e in events)
    assert any(e.type == "error_repair" for e in events)


def test_levelt_abandoned_clause_breakdown():
    """Verify syntactic breakdown with conjunctive particle is flagged as abandoned."""
    analyzer = SelfRepairAnalyzer()

    transcript = "昨日は雨が降っていたので、"
    events, summary = analyzer.analyze(transcript)

    assert summary["abandoned_count"] == 1
    assert summary["abandoned_rate"] == 1.0
    assert summary["monitoring_quality"] == "frequent_breakdowns"
