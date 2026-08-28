import io
import math
import struct
import wave
import numpy as np
import pytest

from app.domains.pronunciation.analyzers.intonation_analyzer import IntonationAnalyzer
from app.domains.pronunciation.analyzers.mora_timing_analyzer import MoraTimingAnalyzer
from app.domains.pronunciation.analyzers.phoneme_analyzer import PhonemeAnalyzer
from app.domains.pronunciation.analyzers.pitch_analyzer import PitchAnalyzerComponent
from app.domains.pronunciation.analyzers.rhythm_analyzer import RhythmAnalyzer
from app.domains.pronunciation.contracts import (
    AnalysisConfidenceLevel,
    PronunciationAnalysisPolicy,
    PronunciationResult,
    PronunciationTarget,
    ReferenceType,
    TargetType,
)
from app.domains.pronunciation.feedback.feedback_generator import PronunciationFeedbackGenerator
from app.domains.pronunciation.infrastructure.alignment_engine import AlignmentEngine
from app.domains.pronunciation.infrastructure.audio_preprocessor import AudioPreprocessor
from app.domains.pronunciation.infrastructure.audio_quality_analyzer import AudioQualityAnalyzer
from app.domains.pronunciation.infrastructure.pitch_extractor import PitchExtractor
from app.domains.pronunciation.infrastructure.vad_analyzer import VADAnalyzer
from app.domains.pronunciation.pipeline import PronunciationPipeline


def create_synthetic_wav(
    duration_sec: float = 1.5,
    freq_hz: float = 220.0,
    sample_rate: int = 16000,
    amplitude: float = 0.5,
    silence_leading_sec: float = 0.1,
    silence_trailing_sec: float = 0.1,
    add_noise: bool = False,
) -> bytes:
    """Generates synthetic 16-bit PCM WAV audio for testing."""
    total_samples = int(duration_sec * sample_rate)
    leading_samples = int(silence_leading_sec * sample_rate)
    trailing_samples = int(silence_trailing_sec * sample_rate)
    tone_samples = max(0, total_samples - leading_samples - trailing_samples)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        raw_data = bytearray()
        # Leading silence
        for _ in range(leading_samples):
            raw_data.extend(struct.pack("<h", 0))

        # Tone
        for i in range(tone_samples):
            val = math.sin(2.0 * math.pi * freq_hz * (i / sample_rate)) * amplitude
            if add_noise:
                val += (np.random.rand() - 0.5) * 0.1
            val = max(-1.0, min(1.0, val))
            sample_val = int(val * 32767.0)
            raw_data.extend(struct.pack("<h", sample_val))

        # Trailing silence
        for _ in range(trailing_samples):
            raw_data.extend(struct.pack("<h", 0))

        wf.writeframes(raw_data)

    return buf.getvalue()


def test_audio_preprocessor_and_vad():
    wav_bytes = create_synthetic_wav(duration_sec=1.2, freq_hz=200.0, amplitude=0.4)
    samples, sr, dur = AudioPreprocessor.load_and_preprocess(wav_bytes)

    assert sr == 16000
    assert 1.0 <= dur <= 1.4
    assert len(samples) > 0
    assert np.max(np.abs(samples)) > 0.1

    vad = VADAnalyzer.analyze(samples, sr)
    assert vad["total_speech_ms"] > 500
    assert len(vad["speech_segments"]) >= 1


def test_audio_quality_analyzer_validation():
    # Clean audio
    clean_wav = create_synthetic_wav(duration_sec=1.5, freq_hz=220.0, amplitude=0.4)
    samples, sr, _ = AudioPreprocessor.load_and_preprocess(clean_wav)
    clean_report = AudioQualityAnalyzer.analyze_quality(samples, sr)
    assert clean_report.is_usable is True
    assert clean_report.signal_level_rms > 0.05

    # Empty audio
    empty_samples = np.zeros(100, dtype=np.float32)
    empty_report = AudioQualityAnalyzer.analyze_quality(empty_samples, sr)
    assert empty_report.is_usable is False
    assert len(empty_report.issues) > 0


def test_pitch_extractor_f0():
    # 220 Hz clean sine wave
    wav_bytes = create_synthetic_wav(duration_sec=1.0, freq_hz=220.0, amplitude=0.5)
    samples, sr, _ = AudioPreprocessor.load_and_preprocess(wav_bytes)

    pitch_curve = PitchExtractor.extract_f0(samples, sr)
    assert pitch_curve.confidence > 0.7
    assert pitch_curve.voiced_ratio > 0.5
    assert pitch_curve.speaker_f0_mean is not None
    assert 200.0 <= pitch_curve.speaker_f0_mean <= 240.0


def test_alignment_engine_proportional():
    alignment = AlignmentEngine.align(
        target_text="がっこう",
        speech_start_ms=100,
        speech_end_ms=900,
    )
    assert alignment.confidence_level == AnalysisConfidenceLevel.HIGH
    assert len(alignment.mora_units) == 4
    # Sokuon (っ) and long vowel (う) should have valid duration values
    assert alignment.mora_units[1].kana == "っ"
    assert alignment.mora_units[1].actual_duration_ms > 0
    assert alignment.mora_units[3].kana == "う"


@pytest.mark.asyncio
async def test_pronunciation_pipeline_end_to_end():
    audio_bytes = create_synthetic_wav(duration_sec=1.6, freq_hz=220.0, amplitude=0.4)
    target = PronunciationTarget(
        reference_text="がっこう",
        expected_reading="がっこう",
        target_type=TargetType.WORD,
        reference_type=ReferenceType.SYNTHETIC,
    )

    result: PronunciationResult = await PronunciationPipeline.run(
        audio_bytes=audio_bytes,
        target=target,
        user_transcript="がっこう",
        policy=PronunciationAnalysisPolicy.DEEP,
    )

    assert result.overall_score > 0.0
    assert result.overall_confidence in [AnalysisConfidenceLevel.HIGH, AnalysisConfidenceLevel.MEDIUM]
    assert result.phoneme_score is not None
    assert result.mora_timing_score is not None
    assert result.pitch_score is not None
    assert result.rhythm_score is not None
    assert result.intonation_score is not None
    assert len(result.strengths) >= 0
    assert result.engine_version == "1.0.0"
