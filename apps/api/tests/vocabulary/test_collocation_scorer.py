import pytest
from app.domains.vocabulary.collocation_scorer import JapaneseCollocationScorer


def test_npmi_mathematical_properties():
    """Verify NPMI boundaries in [-1.0, 1.0] and sensitivity to correlation."""
    # Strong co-occurrence: P(u)=0.01, P(v)=0.01, P(uv)=0.008 (80% overlap)
    npmi_high = JapaneseCollocationScorer.calculate_npmi(0.01, 0.01, 0.008)
    assert 0.7 <= npmi_high <= 1.0

    # Independence: P(uv) = P(u) * P(v)
    npmi_indep = JapaneseCollocationScorer.calculate_npmi(0.1, 0.1, 0.01)
    assert abs(npmi_indep) < 1e-4

    # Repelled / extremely rare co-occurrence
    npmi_low = JapaneseCollocationScorer.calculate_npmi(0.1, 0.1, 0.0001)
    assert npmi_low < 0.0


def test_dunning_llr_contingency():
    """Verify Dunning Log-Likelihood Ratio calculation."""
    # High contingency significance
    llr = JapaneseCollocationScorer.calculate_dunning_llr(k11=50, k12=10, k21=5, k22=1000)
    assert llr > 3.841  # Significant at p < 0.05


def test_analyze_text_detects_unnatural_collocation():
    """Verify detection of common non-native verb-noun pairings."""
    # 1. kaze o ukeru -> should recommend kaze o hiku
    res_kaze = JapaneseCollocationScorer.analyze_text("昨日から風邪を受けて体調が悪いです。")
    assert res_kaze.has_unnatural_collocation is True
    assert res_kaze.overall_naturalness_score < 70.0
    assert len(res_kaze.diagnostics) >= 1

    diag_kaze = res_kaze.diagnostics[0]
    assert diag_kaze.noun == "風邪"
    assert diag_kaze.recommended_verb == "ひく"
    assert "ひく" in diag_kaze.recommended_phrase

    # 2. ocha o tsukuru -> should recommend ocha o ireru
    res_ocha = JapaneseCollocationScorer.analyze_text("美味しいお茶を作ってください。")
    assert res_ocha.has_unnatural_collocation is True
    assert any(d.noun == "お茶" and d.recommended_verb == "淹れる" for d in res_ocha.diagnostics)


def test_analyze_text_rewards_natural_collocations():
    """Verify high naturalness score on authentic native collocations."""
    res = JapaneseCollocationScorer.analyze_text("雨が降ってきたので、傘をさして駅まで歩きました。")
    assert res.has_unnatural_collocation is False
    assert res.overall_naturalness_score >= 90.0
    assert any(d.noun == "傘" and d.is_natural for d in res.diagnostics)
