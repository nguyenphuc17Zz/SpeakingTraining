import pytest
from app.domains.learner_memory.level_assessor import LevelAssessor


def test_mirt_bayesian_level_assessor():
    """Verify MIRT Bayesian MAP correctly calculates continuous latent traits and CEFR mappings."""
    # Advanced learner with many sessions, low errors, fast response, high scores
    adv_res = LevelAssessor.assess_levels(
        total_sessions=20,
        total_turns=120,
        avg_session_score=92.0,
        must_fix_rate=0.02,
        total_corrections_rate=0.10,
        avg_response_speed_ms=1100.0,
        weaknesses_count=1,
        strengths_count=8,
    )

    assert adv_res["level_confidence"] == "high"
    assert adv_res["confidence_score"] >= 0.85
    assert adv_res["overall_level"] in ("upper_intermediate", "advanced")
    assert "latent_traits" in adv_res
    assert adv_res["latent_traits"]["theta_overall"] > 0.5
    assert adv_res["standard_error"] < 0.6  # High confidence has low standard error

    # Beginner learner with high error rate, sluggish speed, low score
    beg_res = LevelAssessor.assess_levels(
        total_sessions=4,
        total_turns=15,
        avg_session_score=55.0,
        must_fix_rate=0.85,
        total_corrections_rate=1.20,
        avg_response_speed_ms=3800.0,
        weaknesses_count=6,
        strengths_count=0,
    )

    assert beg_res["overall_level"] in ("beginner", "elementary")
    assert beg_res["latent_traits"]["theta_overall"] < 0.0
    assert beg_res["latent_traits"]["theta_grammar"] < -0.5
