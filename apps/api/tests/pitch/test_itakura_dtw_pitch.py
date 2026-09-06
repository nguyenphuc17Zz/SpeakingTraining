import pytest
from app.domains.pitch.acoustic.dtw_pitch import DTWPitchEngine


def test_itakura_dtw_pitch_identical_patterns():
    """Verify identical pitch patterns produce distance 0.0 and score 100%."""
    # Atamaka (H L L) Tokyo pattern: [1.5, -1.5, -1.5]
    seq_a = [1.5, -1.5, -1.5]
    seq_b = [1.5, -1.5, -1.5]

    dist, path_len = DTWPitchEngine.compute_dtw_distance(seq_a, seq_b)
    assert dist == 0.0
    assert path_len == 3


def test_itakura_dtw_pitch_inverted_penalty():
    """Verify opposite accent patterns (Heiban vs Atamaka) receive high distance penalty."""
    # Heiban: L H H -> [-1.5, 1.5, 1.5]
    heiban = [-1.5, 1.5, 1.5]
    # Atamaka: H L L -> [1.5, -1.5, -1.5]
    atamaka = [1.5, -1.5, -1.5]

    dist, path_len = DTWPitchEngine.compute_dtw_distance(heiban, atamaka)
    assert dist >= 1.5

    res = DTWPitchEngine.compute_pitch_contour_similarity(heiban, ["H", "L", "L"])
    assert res.similarity_score < 60.0


def test_itakura_dtw_similarity_scoring():
    """Verify similarity scoring is bounded in [10, 100]."""
    obs = [-1.2, 1.4, 1.6, -1.3]
    res = DTWPitchEngine.compute_pitch_contour_similarity(obs, ["L", "H", "H", "L"])
    assert 70.0 <= res.similarity_score <= 100.0
    assert res.normalized_distance < 1.0
