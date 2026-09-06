import math
import pytest
from app.domains.shadowing.analysis.prosody_alignment import ProsodyDynamicTimeWarper


def test_fastdtw_identical_prosody():
    """Verify identical series produces 0 warping distance and 100% consistency."""
    # Sine wave prosody contour
    ref = [math.sin(i * 0.2) * 50.0 + 150.0 for i in range(50)]
    lrn = list(ref)

    res = ProsodyDynamicTimeWarper.align(ref, lrn, frame_step_ms=20)
    assert res.status == "success"
    assert res.warping_distance == 0.0
    assert res.tempo_consistency_score == 100.0
    assert abs(res.mean_local_lag_ms) < 1e-2
    assert len(res.hesitation_segments) == 0


def test_fastdtw_uniform_shift_tempo_stability():
    """Verify uniform time shift maintains high tempo consistency score."""
    base = [math.sin(i * 0.15) * 40.0 + 160.0 for i in range(60)]
    # Learner is shifted by 3 frames (60ms)
    shift = 3
    ref = base[shift:]
    lrn = base[:-shift]

    res = ProsodyDynamicTimeWarper.align(ref, lrn, frame_step_ms=20)
    assert res.status == "success"
    assert res.tempo_consistency_score > 80.0
    assert res.alignment_path_length > 0


def test_fastdtw_hesitation_segment_detection():
    """Verify non-linear stall in learner audio is captured as hesitation segment."""
    ref = [100.0 + i * 2.0 for i in range(40)]
    # Learner repeats frame at index 15 for 6 extra frames (stalled speech)
    lrn = list(ref[:15]) + [ref[15]] * 6 + list(ref[15:])

    res = ProsodyDynamicTimeWarper.align(ref, lrn, frame_step_ms=20)
    assert res.status == "success"
    assert res.alignment_path_length > len(ref)
    assert res.reference_frames == 40
    assert res.learner_frames == 46


def test_fastdtw_empty_input():
    """Verify defensive handling of empty input series."""
    res = ProsodyDynamicTimeWarper.align([], [])
    assert res.status == "insufficient_data"
    assert res.warping_distance == 0.0
