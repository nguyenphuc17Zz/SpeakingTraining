import io
import wave
import numpy as np
import pytest
from app.domains.audio.contracts import AudioQualityStatus
from app.domains.audio.recording_service import AudioQualityAnalyzer


def create_test_wav(samples: np.ndarray, sample_rate: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        # Convert float (-1.0 to 1.0) to int16
        int_samples = (np.clip(samples, -1.0, 1.0) * 32767.0).astype(np.int16)
        wf.writeframes(int_samples.tobytes())
    return buf.getvalue()


def test_audio_quality_silent_empty():
    report = AudioQualityAnalyzer.analyze(b"")
    assert report.quality == AudioQualityStatus.SILENT
    assert report.duration_ms == 0


def test_audio_quality_normal_sine_wave():
    sr = 16000
    t = np.linspace(0, 0.6, int(sr * 0.6), endpoint=False)
    # 440Hz sine wave at moderate volume (0.3 amplitude = ~ -10dB) with initial silence
    silence = np.zeros(int(sr * 0.2), dtype=np.float32)
    sine = 0.3 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    samples = np.concatenate([silence, sine, silence])
    wav_bytes = create_test_wav(samples, sr)

    report = AudioQualityAnalyzer.analyze(wav_bytes)
    assert report.duration_ms == 1000
    assert report.has_clipping is False
    assert report.quality in [AudioQualityStatus.GOOD, AudioQualityStatus.ACCEPTABLE]


def test_audio_quality_clipping_detection():
    sr = 16000
    # Create heavily clipping signal (amplitude 1.5 clipped)
    samples = np.ones(sr, dtype=np.float32) * 0.99
    wav_bytes = create_test_wav(samples, sr)

    report = AudioQualityAnalyzer.analyze(wav_bytes)
    assert report.has_clipping is True
    assert report.quality == AudioQualityStatus.CLIPPING
    assert len(report.warnings) > 0
