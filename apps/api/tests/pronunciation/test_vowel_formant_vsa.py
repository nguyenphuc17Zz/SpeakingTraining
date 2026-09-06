import numpy as np
import pytest

from app.domains.pronunciation.analyzers.vowel_formant_analyzer import VowelFormantAnalyzer


def test_levinson_durbin_and_lpc_formant_extraction():
    # 1. Synthesize a signal with known resonance peaks (e.g. F1=800Hz, F2=1300Hz at 16kHz)
    sr = 16000
    duration = 0.05  # 50ms
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # Impulse train + resonant filtering approximation
    f0 = 120.0
    signal = np.sin(2 * np.pi * f0 * t)
    # Add formant harmonics
    signal += 0.8 * np.sin(2 * np.pi * 800 * t) * np.exp(-t * 80)
    signal += 0.6 * np.sin(2 * np.pi * 1300 * t) * np.exp(-t * 100)

    formants = VowelFormantAnalyzer.extract_lpc_formants(signal, sample_rate=sr, order=18)
    assert len(formants) >= 1
    # Check that formant frequencies are within human vocal tract ranges
    for freq, bw in formants:
        assert 180.0 <= freq <= 4000.0
        assert bw < 650.0


def test_vsa_and_fcr_calculation():
    # Reference Tokyo Japanese vowel formants
    ref_coords = VowelFormantAnalyzer.REFERENCE_FORMANTS
    assessment = VowelFormantAnalyzer.assess_vowel_space(ref_coords)

    # VSA should be positive and substantial (~200,000 to 450,000 Hz^2)
    assert 200000.0 <= assessment.vsa_hz2 <= 500000.0
    # Reference FCR should be around 0.95 - 1.02
    assert 0.90 <= assessment.fcr <= 1.05
    assert assessment.vowel_dispersion_status in ("natural", "expanded_crisp")
    assert assessment.articulation_clarity_score >= 80.0

    # Test Centralized (Muddled / Slurred) Articulation
    centralized_coords = {
        "a": (580.0, 1400.0),  # /a/ is under-opened
        "i": (380.0, 1900.0),  # /i/ is centralized
        "u": (420.0, 1450.0),
        "e": (500.0, 1600.0),
        "o": (480.0, 1200.0),
    }
    muddled_assessment = VowelFormantAnalyzer.assess_vowel_space(centralized_coords)
    assert muddled_assessment.vsa_hz2 < assessment.vsa_hz2
    assert muddled_assessment.fcr > assessment.fcr
    assert muddled_assessment.articulation_clarity_score < assessment.articulation_clarity_score
    assert muddled_assessment.vowel_dispersion_status in ("mild_centralization", "compressed_slurred")


def test_japanese_vowel_devoicing():
    # Test unvoiced mora in standard environments
    assert VowelFormantAnalyzer.detect_devoicing_environment("す", is_voiced_acoustic=False, is_phrase_final=True)
    assert VowelFormantAnalyzer.detect_devoicing_environment("き", is_voiced_acoustic=False, is_phrase_final=False)
    assert VowelFormantAnalyzer.detect_devoicing_environment("し", is_voiced_acoustic=False, is_phrase_final=False)

    # Voiced vowels / non-devoicing kana
    assert not VowelFormantAnalyzer.detect_devoicing_environment("あ", is_voiced_acoustic=False)
    assert not VowelFormantAnalyzer.detect_devoicing_environment("ま", is_voiced_acoustic=False)
