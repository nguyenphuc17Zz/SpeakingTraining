import pytest
from app.domains.pitch.acoustic.dtw_pitch import DTWPitchEngine


def test_dtw_perfect_match():
    """Verify identical pitch contours produce ~100% similarity and 0 distance."""
    pattern = ["L", "H", "H", "L"]
    # Observed semitones matching L (-1.5), H (+1.5), H (+1.5), L (-1.5)
    observed = [-1.5, 1.5, 1.5, -1.5]

    result = DTWPitchEngine.compute_pitch_contour_similarity(
        observed_mora_semitones=observed,
        expected_pattern=pattern,
    )

    assert result.similarity_score >= 95.0
    assert result.normalized_distance < 0.2
    assert "DTW" in result.alignment_summary


def test_dtw_inverted_contour_penalized():
    """Verify inverted pitch contours (e.g. Atamadaka H-L-L vs Odaka L-H-H) produce low similarity."""
    expected_pattern = ["H", "L", "L"]
    # User pronounced inverse pattern L-H-H
    observed = [-2.0, 1.8, 1.8]

    result = DTWPitchEngine.compute_pitch_contour_similarity(
        observed_mora_semitones=observed,
        expected_pattern=expected_pattern,
    )

    assert result.similarity_score <= 55.0
    assert result.normalized_distance > 1.5


def test_speaker_invariance_male_female():
    """
    Verify DTWPitchEngine converts Hz to semitones with speaker pitch invariance:
    A male octave lower (120Hz -> 170Hz) has identical semitone delta to a female (240Hz -> 340Hz).
    """
    male_f0 = [120.0, 170.0, 170.0]
    female_f0 = [240.0, 340.0, 340.0]

    male_st = DTWPitchEngine.hz_to_semitones(male_f0)
    female_st = DTWPitchEngine.hz_to_semitones(female_f0)

    # Relative semitone differences should match within 0.05 st
    male_delta = male_st[1] - male_st[0]
    female_delta = female_st[1] - female_st[0]

    assert abs(male_delta - female_delta) < 0.05


def test_dtw_mismatched_lengths():
    """Verify DTW aligns sequences of different lengths (warping in time)."""
    # 3 moras vs 4 moras
    seq_a = [-1.5, 1.5, 1.5]
    seq_b = [-1.5, 1.5, 1.5, 1.5]

    dist, path_len = DTWPitchEngine.compute_dtw_distance(seq_a, seq_b)
    assert dist < 0.5
    assert path_len >= 4
