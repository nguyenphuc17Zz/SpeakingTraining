import pytest
from app.domains.monologue.analytics.discourse_analyzer import DiscourseStructureAnalyzer


def test_centering_theory_consistent_topic_continue():
    """Verify consistent topic discourse produces CONTINUE transitions and high cohesion."""
    # Cohesive monologue keeping topic "テレワーク"
    text = (
        "テレワークは時間を有効に使えます。"
        "テレワークは通勤のストレスを減らします。"
        "テレワークは家族との時間を増やします。"
    )
    res = DiscourseStructureAnalyzer.compute_centering_cohesion(text)

    assert res["cohesion_flow_score"] >= 85.0
    assert (res["transition_distribution"]["CONTINUE"] + res["transition_distribution"]["RETAIN"]) >= 2
    assert res["dominant_transition"] in ("CONTINUE", "RETAIN")


def test_centering_theory_abrupt_shift():
    """Verify disconnected topics produce ROUGH_SHIFT transitions and lower cohesion."""
    # Fragmented monologue jumping randomly between unrelated subjects
    text = (
        "猫は魚が好きです。"
        "宇宙船は火星に向かいます。"
        "数学は難しいです。"
    )
    res = DiscourseStructureAnalyzer.compute_centering_cohesion(text)

    assert res["transition_distribution"]["ROUGH_SHIFT"] >= 1
    assert res["cohesion_flow_score"] < 70.0


def test_coherence_score_integration_with_centering():
    """Verify coherence_score integrates centering_cohesion without breaking contracts."""
    da = DiscourseStructureAnalyzer()
    text = "私はテレワークに賛成です。理由は便利だからです。例えば通勤が不要です。結論として良いです。"
    discourse = da.analyze(text, "opinion")
    score = da.coherence_score(None, discourse, transcript=text)

    assert "overall" in score
    assert "topic_continuity" in score
    assert "centering_cohesion" in score
    assert score["overall"] > 0
