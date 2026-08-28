"""PitchExtractor — wraps existing + librosa pyin / parselmouth guarded.

Reuses infrastructure/pitch_extractor.py autocorr as fallback.
Primary: librosa.pyin (fmin 60, fmax 500), secondary: parselmouth.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from app.core.logging import logger
from app.domains.pronunciation.infrastructure.pitch_extractor import PitchExtractor as BasePitchExtractor
from app.domains.pronunciation.contracts import PitchCurve, PitchPoint


class PitchExtractor:
    F0_MIN = 60
    F0_MAX = 500

    def __init__(self):
        self._base = BasePitchExtractor()
        self._librosa_available = False
        self._parselmouth_available = False
        try:
            import librosa  # type: ignore

            self._librosa_available = True
        except Exception:
            pass
        try:
            import parselmouth  # type: ignore

            self._parselmouth_available = True
        except Exception:
            pass

    def extract(self, samples: np.ndarray, sr: int = 16000) -> PitchCurve:
        # Try librosa pyin first if available
        if self._librosa_available:
            try:
                return self._extract_librosa(samples, sr)
            except Exception as e:
                logger.warning(f"[PitchExtractor] librosa failed {e}, fallback to base")
        if self._parselmouth_available:
            try:
                return self._extract_parselmouth(samples, sr)
            except Exception as e:
                logger.warning(f"[PitchExtractor] parselmouth failed {e}, fallback to base")
        # Fallback to base autocorr
        return self._base.extract_f0(samples, sr)

    def _extract_librosa(self, samples: np.ndarray, sr: int) -> PitchCurve:
        import librosa

        # librosa.pyin expects float32 in -1..1
        y = samples.astype(np.float32)
        # hop 10ms = 0.01*sr, frame 20ms
        hop_length = int(0.01 * sr)
        f0, voiced_flag, voiced_prob = librosa.pyin(
            y, fmin=self.F0_MIN, fmax=self.F0_MAX, sr=sr, hop_length=hop_length, frame_length=int(0.02 * sr)
        )
        # f0 contains nan for unvoiced
        # Build PitchCurve
        points: list[PitchPoint] = []
        # Median for normalization
        voiced_f0s = f0[~np.isnan(f0)]
        median = float(np.median(voiced_f0s)) if len(voiced_f0s) > 0 else 120.0
        mean = float(np.mean(voiced_f0s)) if len(voiced_f0s) > 0 else median
        std = float(np.std(voiced_f0s)) if len(voiced_f0s) > 1 else 20.0
        for i, (f, prob, flag) in enumerate(zip(f0, voiced_prob, voiced_flag)):
            t_ms = i * 10  # hop 10ms
            is_voiced = bool(flag) and not math.isnan(f) and f > 0
            freq = float(f) if is_voiced else 0.0
            # semitone relative to median
            if is_voiced:
                semitone = 12 * math.log2(freq / median) if median > 0 else 0.0
            else:
                semitone = 0.0
            points.append(
                PitchPoint(
                    timestamp_ms=float(t_ms),
                    frequency_hz=freq,
                    normalized_semitones=float(semitone),
                    is_voiced=is_voiced,
                    confidence=float(prob) if not math.isnan(prob) else 0.5,
                )
            )
        voiced_ratio = float(np.mean(voiced_flag)) if len(voiced_flag) > 0 else 0.0
        confidence = 0.92 if voiced_ratio > 0.3 and len(voiced_f0s) > 10 else 0.6 if voiced_ratio > 0.15 else 0.3
        return PitchCurve(
            points=points,
            speaker_f0_mean=mean,
            speaker_f0_std=std,
            voiced_ratio=voiced_ratio,
            confidence=confidence,
            normalization_method="semitone_median_relative",
        )

    def _extract_parselmouth(self, samples: np.ndarray, sr: int) -> PitchCurve:
        import parselmouth

        # parselmouth expects Sound
        snd = parselmouth.Sound(samples, sampling_frequency=sr)
        pitch = snd.to_pitch(time_step=0.01, pitch_floor=self.F0_MIN, pitch_ceiling=self.F0_MAX)
        # Extract f0 per frame
        n_frames = pitch.get_number_of_frames()
        points: list[PitchPoint] = []
        f0s = []
        for i in range(1, n_frames + 1):
            t = pitch.get_time_from_frame_number(i)
            f = pitch.get_value_in_frame(i)
            is_voiced = f is not None and not math.isnan(f) and f > 0
            f_val = float(f) if is_voiced else 0.0
            if is_voiced:
                f0s.append(f_val)
            points.append(
                PitchPoint(
                    timestamp_ms=float(t * 1000),
                    frequency_hz=f_val,
                    normalized_semitones=0.0,  # fill after median
                    is_voiced=is_voiced,
                    confidence=0.85 if is_voiced else 0.2,
                )
            )
        median = float(np.median(f0s)) if f0s else 120.0
        mean = float(np.mean(f0s)) if f0s else median
        std = float(np.std(f0s)) if len(f0s) > 1 else 20.0
        for p in points:
            if p.is_voiced and p.frequency_hz > 0:
                p.normalized_semitones = 12 * math.log2(p.frequency_hz / median) if median > 0 else 0.0
        voiced_ratio = len(f0s) / max(1, n_frames)
        confidence = 0.90 if voiced_ratio > 0.3 else 0.6 if voiced_ratio > 0.15 else 0.3
        return PitchCurve(
            points=points,
            speaker_f0_mean=mean,
            speaker_f0_std=std,
            voiced_ratio=voiced_ratio,
            confidence=confidence,
            normalization_method="semitone_median_relative",
        )
