import io
import wave
import numpy as np
import pytest

from app.domains.audio.recording_service import AudioQualityAnalyzer, OtsuVADTrimmer


def _generate_wav_with_silence(head_silence_s: float, speech_s: float, tail_silence_s: float, sr: int = 16000) -> bytes:
    """Generates synthetic PCM WAV with silence - sine wave tone (speech) - silence."""
    head_len = int(head_silence_s * sr)
    speech_len = int(speech_s * sr)
    tail_len = int(tail_silence_s * sr)

    # Low noise for silence
    head = np.random.normal(0, 0.001, head_len).astype(np.float32)
    # Loud sine tone for speech
    t = np.linspace(0, speech_s, speech_len)
    speech = (0.5 * np.sin(2 * np.pi * 440.0 * t) + np.random.normal(0, 0.01, speech_len)).astype(np.float32)
    tail = np.random.normal(0, 0.001, tail_len).astype(np.float32)

    full = np.concatenate([head, speech, tail])
    pcm16 = (full * 32767.0).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm16.tobytes())
    return buf.getvalue()


def test_otsu_vad_trimming_synthetic():
    """Verify Otsu VAD detects speech boundaries and trims leading/trailing silence."""
    wav_bytes = _generate_wav_with_silence(head_silence_s=1.0, speech_s=1.5, tail_silence_s=1.0)

    report = AudioQualityAnalyzer.analyze(wav_bytes)

    assert report.duration_ms >= 3400
    assert report.head_silence_ms is not None
    assert report.head_silence_ms >= 700  # detected around 1s head silence
    assert report.tail_silence_ms is not None
    assert report.tail_silence_ms >= 700  # detected around 1s tail silence
    assert report.trimmed_duration_ms is not None
    assert report.trimmed_duration_ms < report.duration_ms
    assert report.voice_activity_ratio is not None
    assert 0.20 <= report.voice_activity_ratio <= 0.65


def test_otsu_vad_pure_silence():
    """Verify pure silence is handled gracefully without crash."""
    silence_wav = _generate_wav_with_silence(head_silence_s=0.5, speech_s=0.0, tail_silence_s=0.5)
    report = AudioQualityAnalyzer.analyze(silence_wav)
    assert report.voice_activity_ratio == 0.0 or report.trimmed_duration_ms is not None
