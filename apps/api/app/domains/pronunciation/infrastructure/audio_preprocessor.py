import io
import math
import struct
import wave
from typing import Any
import numpy as np

from app.core.logging import logger

try:
    import av
    _AV_AVAILABLE = True
except Exception:
    _AV_AVAILABLE = False

try:
    from scipy.signal import resample_poly
    _SCIPY_RESAMPLE_AVAILABLE = True
except Exception:
    _SCIPY_RESAMPLE_AVAILABLE = False


class AudioPreprocessor:
    """Preprocesses raw audio bytes (WebM, Opus, WAV, MP3, OGG, etc.) into normalized 16kHz mono float32 numpy arrays."""

    TARGET_SAMPLE_RATE = 16000

    @classmethod
    def load_and_preprocess(cls, audio_bytes: bytes) -> tuple[np.ndarray, int, float]:
        """
        Decodes audio bytes from any container (WebM, WAV, MP3, OGG),
        resamples to 16kHz mono float32 array, and applies gentle normalization.
        Returns:
            - float32 numpy array (samples in range [-1.0, 1.0])
            - sample_rate (16000)
            - duration_seconds
        """
        if not audio_bytes or len(audio_bytes) < 32:
            return np.zeros(0, dtype=np.float32), cls.TARGET_SAMPLE_RATE, 0.0

        # Method 1: Use PyAV (av) - Universal High-Speed Decoder for WebM/Opus/MP3/WAV
        if _AV_AVAILABLE:
            try:
                container = av.open(io.BytesIO(audio_bytes))
                audio_streams = [s for s in container.streams if s.type == "audio"]
                if audio_streams:
                    resampler = av.AudioResampler(
                        format="fltp",
                        layout="mono",
                        rate=cls.TARGET_SAMPLE_RATE,
                    )
                    all_frames = []
                    for frame in container.decode(audio_streams[0]):
                        for resampled_frame in resampler.resample(frame):
                            all_frames.append(resampled_frame.to_ndarray()[0])

                    if all_frames:
                        samples = np.concatenate(all_frames).astype(np.float32)

                        # Gentle peak normalization
                        max_abs = np.max(np.abs(samples)) if len(samples) > 0 else 0.0
                        if 0.001 < max_abs < 0.90:
                            gain = min(0.90 / max_abs, 4.0)
                            samples = samples * gain

                        duration_sec = len(samples) / float(cls.TARGET_SAMPLE_RATE)
                        return samples, cls.TARGET_SAMPLE_RATE, duration_sec
            except Exception as e:
                logger.debug(f"[AudioPreprocessor] PyAV decode attempt notice: {e}. Trying wave fallback...")

        # Method 2: Standard WAV fallback
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                num_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                sample_rate = wf.getframerate()
                num_frames = wf.getnframes()
                raw_frames = wf.readframes(num_frames)

            # Convert raw bytes to numpy array according to sample width
            if sample_width == 2:  # 16-bit PCM
                samples = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32) / 32768.0
            elif sample_width == 1:  # 8-bit PCM
                samples = (np.frombuffer(raw_frames, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
            elif sample_width == 4:  # 32-bit PCM or float
                samples = np.frombuffer(raw_frames, dtype=np.int32).astype(np.float32) / 2147483648.0
            else:
                samples = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32) / 32768.0

            # Convert stereo to mono
            if num_channels > 1:
                samples = samples.reshape(-1, num_channels).mean(axis=1)

            # Resample to 16kHz if different
            if sample_rate != cls.TARGET_SAMPLE_RATE and len(samples) > 0:
                samples = cls._resample(samples, sample_rate, cls.TARGET_SAMPLE_RATE)
                sample_rate = cls.TARGET_SAMPLE_RATE

            # Gentle amplitude normalization
            max_abs = np.max(np.abs(samples)) if len(samples) > 0 else 0.0
            if 0.001 < max_abs < 0.90:
                gain = min(0.90 / max_abs, 4.0)
                samples = samples * gain

            duration_sec = len(samples) / float(sample_rate) if sample_rate > 0 else 0.0
            return samples.astype(np.float32), sample_rate, duration_sec

        except Exception as e:
            logger.warning(f"[AudioPreprocessor] Error reading audio bytes: {e}. Generating empty array.")
            return np.zeros(0, dtype=np.float32), cls.TARGET_SAMPLE_RATE, 0.0

    @classmethod
    def _resample(cls, samples: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resamples 1D audio array from orig_sr to target_sr."""
        if orig_sr == target_sr or len(samples) == 0:
            return samples

        gcd = math.gcd(orig_sr, target_sr)
        up = target_sr // gcd
        down = orig_sr // gcd

        if _SCIPY_RESAMPLE_AVAILABLE:
            try:
                return resample_poly(samples, up, down).astype(np.float32)
            except Exception:
                pass

        # Linear interpolation fallback
        orig_len = len(samples)
        target_len = int(round(orig_len * (target_sr / float(orig_sr))))
        if target_len <= 0:
            return np.zeros(0, dtype=np.float32)
        orig_indices = np.linspace(0, orig_len - 1, orig_len)
        target_indices = np.linspace(0, orig_len - 1, target_len)
        return np.interp(target_indices, orig_indices, samples).astype(np.float32)

