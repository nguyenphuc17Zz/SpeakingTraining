import pytest
from app.domains.speech.adapters.faster_whisper import PlattConfidenceCalibrator


def test_platt_probability_softening_overconfidence():
    """Verify extreme raw probabilities are softened to realistic calibrated bounds."""
    # Extremely high raw probability (e.g. 0.999) is calibrated to ~0.98
    p_high = PlattConfidenceCalibrator.calibrate_probability(0.999)
    assert 0.95 <= p_high <= 0.99

    # Mid-range probability (0.50) remains unbiased around 0.50
    p_mid = PlattConfidenceCalibrator.calibrate_probability(0.50)
    assert 0.48 <= p_mid <= 0.52

    # Low probability (0.05) is calibrated cleanly
    p_low = PlattConfidenceCalibrator.calibrate_probability(0.05)
    assert 0.05 <= p_low <= 0.20


def test_platt_logprob_calibration():
    """Verify logprob calibration maps log-likelihood smoothly to (0.0, 1.0)."""
    # High confidence logprob near 0 (e.g. -0.05)
    c_high = PlattConfidenceCalibrator.calibrate_logprob(-0.05)
    assert c_high >= 0.50

    # Very low confidence logprob (e.g. -2.50)
    c_low = PlattConfidenceCalibrator.calibrate_logprob(-2.50)
    assert c_low < 0.10
    assert c_low >= 0.01
