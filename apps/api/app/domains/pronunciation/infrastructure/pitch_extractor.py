import math
from typing import Any
import numpy as np

from app.core.logging import logger
from app.domains.pronunciation.contracts import PitchCurve, PitchPoint


class PitchExtractor:
    """Extracts fundamental frequency (F0) contour and performs speaker normalization."""

    F0_MIN = 60.0    # Hz (low male pitch limit)
    F0_MAX = 450.0   # Hz (high female/child pitch limit)
    FRAME_MS = 20    # 20ms frame
    HOP_MS = 10      # 10ms hop
    VOICING_THRESHOLD = 0.35  # Autocorrelation peak threshold for voiced detection

    @classmethod
    def extract_f0(cls, samples: np.ndarray, sample_rate: int = 16000) -> PitchCurve:
        """
        Extracts F0 contour across 10ms hop intervals using Normalized Cross-Correlation (NCCF / YIN-like).
        Performs speaker normalization into semitones relative to speaker's median F0.
        """
        if len(samples) < int(sample_rate * 0.05):
            return PitchCurve(points=[], confidence=0.0)

        frame_len = int(sample_rate * (cls.FRAME_MS / 1000.0))
        hop_len = int(sample_rate * (cls.HOP_MS / 1000.0))
        num_frames = max(1, (len(samples) - frame_len) // hop_len)

        min_lag = int(sample_rate / cls.F0_MAX)
        max_lag = int(sample_rate / cls.F0_MIN)

        raw_points: list[dict[str, Any]] = []
        voiced_f0_values: list[float] = []

        for f in range(num_frames):
            start = f * hop_len
            frame = samples[start : start + frame_len]
            timestamp_ms = int((start / float(sample_rate)) * 1000)

            # Energy check
            rms = float(np.sqrt(np.mean(frame**2)))
            if rms < 0.005:
                raw_points.append({
                    "timestamp_ms": timestamp_ms,
                    "frequency_hz": 0.0,
                    "is_voiced": False,
                    "confidence": 1.0,
                })
                continue

            # Normalized Autocorrelation
            f0_val, conf = cls._estimate_f0_autocorr(frame, sample_rate, min_lag, max_lag)

            if f0_val > 0 and conf >= cls.VOICING_THRESHOLD:
                raw_points.append({
                    "timestamp_ms": timestamp_ms,
                    "frequency_hz": f0_val,
                    "is_voiced": True,
                    "confidence": round(conf, 3),
                })
                voiced_f0_values.append(f0_val)
            else:
                raw_points.append({
                    "timestamp_ms": timestamp_ms,
                    "frequency_hz": 0.0,
                    "is_voiced": False,
                    "confidence": round(1.0 - conf, 3),
                })

        if not voiced_f0_values:
            return PitchCurve(
                points=[
                    PitchPoint(
                        timestamp_ms=p["timestamp_ms"],
                        frequency_hz=0.0,
                        normalized_semitones=0.0,
                        is_voiced=False,
                        confidence=p["confidence"],
                    )
                    for p in raw_points
                ],
                speaker_f0_mean=None,
                speaker_f0_std=None,
                voiced_ratio=0.0,
                confidence=0.3,
            )

        # Speaker median & statistics for semitone normalization
        f0_array = np.array(voiced_f0_values)
        median_f0 = float(np.median(f0_array))
        mean_f0 = float(np.mean(f0_array))
        std_f0 = float(np.std(f0_array)) if len(f0_array) > 1 else 10.0

        # Construct final PitchPoint list with speaker-normalized semitones: 12 * log2(F0 / Median_F0)
        pitch_points: list[PitchPoint] = []
        for p in raw_points:
            f0 = p["frequency_hz"]
            is_voiced = p["is_voiced"]
            if is_voiced and f0 > 0 and median_f0 > 0:
                # Relative semitone offset from speaker baseline (e.g. +2.5 semitones or -1.8 semitones)
                semitones = 12.0 * math.log2(f0 / median_f0)
            else:
                semitones = 0.0

            pitch_points.append(
                PitchPoint(
                    timestamp_ms=p["timestamp_ms"],
                    frequency_hz=round(f0, 1),
                    normalized_semitones=round(semitones, 2),
                    is_voiced=is_voiced,
                    confidence=p["confidence"],
                )
            )

        voiced_ratio = len(voiced_f0_values) / float(len(raw_points)) if raw_points else 0.0
        overall_conf = 0.9 if voiced_ratio > 0.3 else 0.5

        return PitchCurve(
            points=pitch_points,
            speaker_f0_mean=round(mean_f0, 1),
            speaker_f0_std=round(std_f0, 1),
            voiced_ratio=round(voiced_ratio, 3),
            confidence=overall_conf,
            normalization_method="semitone_median_relative",
        )

    @classmethod
    def _estimate_f0_autocorr(
        cls, frame: np.ndarray, sr: int, min_lag: int, max_lag: int
    ) -> tuple[float, float]:
        """Calculates normalized autocorrelation peak for pitch estimation with parabolic interpolation."""
        # Subtract mean
        norm_frame = frame - np.mean(frame)
        var = np.sum(norm_frame**2)
        if var < 1e-6:
            return 0.0, 0.0

        # Autocorrelation
        autocorr = np.correlate(norm_frame, norm_frame, mode="full")
        mid = len(autocorr) // 2
        r = autocorr[mid : mid + max_lag + 2]

        if len(r) <= max_lag:
            return 0.0, 0.0

        # Search for peak in [min_lag, max_lag]
        search_region = r[min_lag : max_lag + 1]
        if len(search_region) == 0:
            return 0.0, 0.0

        peak_idx = int(np.argmax(search_region)) + min_lag
        peak_val = r[peak_idx] / var

        if peak_val < cls.VOICING_THRESHOLD:
            return 0.0, float(peak_val)

        # Parabolic interpolation around peak for sub-sample accuracy
        if 0 < peak_idx < len(r) - 1:
            alpha = r[peak_idx - 1]
            beta = r[peak_idx]
            gamma = r[peak_idx + 1]
            denom = 2.0 * (alpha - 2.0 * beta + gamma)
            if abs(denom) > 1e-6:
                delta = (alpha - gamma) / denom
                exact_lag = peak_idx + delta
            else:
                exact_lag = float(peak_idx)
        else:
            exact_lag = float(peak_idx)

        if exact_lag <= 0:
            return 0.0, 0.0

        f0 = sr / exact_lag
        if cls.F0_MIN <= f0 <= cls.F0_MAX:
            return float(f0), float(peak_val)
        return 0.0, 0.0
