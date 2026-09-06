"""Shadowing Acoustic Lag Profiler & Intonation DTW Engine.

Implements cognitive SLA shadowing science (Lambert 1992; Kadota 2007; Tamai 1997):
- Optimal cognitive shadowing lag τ ∈ [150ms, 400ms] (sweet spot ~250ms).
- Penalizes concurrent talking over (< 100ms) and trailing into delayed repeat (> 700ms).
- Dynamic Time Warping (DTW) intonation contour evaluation.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from app.domains.pitch.acoustic.dtw_pitch import DTWPitchEngine


class ShadowingLagProfiler:
    """Acoustic lag and intonation contour profiler for Japanese shadowing."""

    OPTIMAL_LAG_MIN_MS: float = 150.0
    OPTIMAL_LAG_MAX_MS: float = 400.0
    SWEET_SPOT_MS: float = 250.0
    TALKING_OVER_LIMIT_MS: float = 100.0
    TRAILING_LIMIT_MS: float = 700.0

    @classmethod
    def classify_lag(cls, lag_ms: float) -> str:
        """Classifies auditory-vocal shadowing lag into discrete cognitive tiers.

        - 'optimal': 150ms - 400ms (ideal cognitive tracking window)
        - 'too_fast': < 100ms (talking over / concurrent auditory interference)
        - 'hesitant': 100ms - 149ms or 401ms - 700ms (mild hesitation / lag)
        - 'trailing': > 700ms (dropped out of shadowing into sequential repeating)
        """
        if lag_ms < cls.TALKING_OVER_LIMIT_MS:
            return "too_fast"
        if cls.OPTIMAL_LAG_MIN_MS <= lag_ms <= cls.OPTIMAL_LAG_MAX_MS:
            return "optimal"
        if lag_ms <= cls.TRAILING_LIMIT_MS:
            return "hesitant"
        return "trailing"

    @classmethod
    def compute_lag_score(cls, lag_ms: float) -> float:
        """Calculates psychometric lag score [0.0 - 100.0].

        Peak performance at 250ms with a broad plateau over [150ms, 400ms].
        """
        if cls.OPTIMAL_LAG_MIN_MS <= lag_ms <= cls.OPTIMAL_LAG_MAX_MS:
            # Inside optimal plateau: scores 92 - 100
            diff = abs(lag_ms - cls.SWEET_SPOT_MS)
            score = 100.0 - (diff / 150.0) * 8.0
            return round(max(92.0, min(100.0, score)), 1)

        if lag_ms < cls.OPTIMAL_LAG_MIN_MS:
            # Talking over: rapid decay down to ~35% at 0ms
            ratio = max(0.0, lag_ms) / cls.OPTIMAL_LAG_MIN_MS
            score = 35.0 + ratio * 57.0
            return round(max(30.0, min(92.0, score)), 1)

        # Trailing lag > 400ms: Gaussian decay
        delta = lag_ms - cls.OPTIMAL_LAG_MAX_MS
        decay = math.exp(-((delta) ** 2) / (2 * (280.0 ** 2)))
        score = 40.0 + decay * 52.0
        return round(max(25.0, min(92.0, score)), 1)

    @classmethod
    def evaluate_pitch_contour(
        cls,
        user_pitch_curve: Any | None,
        reference_semitones: list[float] | None = None,
    ) -> float | None:
        """Evaluates intonation contour similarity using DTW with Semitone Normalization."""
        if not user_pitch_curve:
            return None

        points = getattr(user_pitch_curve, "points", None)
        if not points:
            return None

        # Extract voiced semitone values
        voiced_semitones = [
            float(p.normalized_semitones)
            for p in points
            if getattr(p, "is_voiced", True) and getattr(p, "normalized_semitones", None) is not None
        ]
        if len(voiced_semitones) < 3:
            return None

        # If explicit reference is provided, run full DTW
        if reference_semitones and len(reference_semitones) >= 3:
            distance, _ = DTWPitchEngine.compute_dtw_distance(voiced_semitones, reference_semitones)
            similarity = round(100.0 * math.exp(-0.45 * distance), 1)
            return max(0.0, min(100.0, similarity))

        # Intonation contour dynamism / stability heuristic: rewards natural pitch fluctuations
        diffs = [abs(voiced_semitones[i] - voiced_semitones[i - 1]) for i in range(1, len(voiced_semitones))]
        avg_diff = sum(diffs) / len(diffs) if diffs else 0.0
        # Natural Japanese sentence intonation has mean frame-to-frame delta ~0.3 - 1.2 semitones
        if 0.25 <= avg_diff <= 1.5:
            dynamic_score = 90.0 + min(10.0, (avg_diff - 0.25) * 8.0)
        else:
            dynamic_score = max(55.0, 90.0 - abs(avg_diff - 0.8) * 25.0)
        return round(dynamic_score, 1)

    @classmethod
    def generate_lag_issue(cls, lag_ms: float, rating: str) -> dict[str, Any] | None:
        """Generates targeted pedagogical recommendation based on cognitive shadowing lag."""
        if rating == "too_fast":
            return {
                "title": "Nói đè lên giọng mẫu (Concurrent Interference)",
                "category": "Độ trễ Shadowing",
                "explanation": (
                    f"Độ trễ phản xạ chỉ {lag_ms:.0f}ms (< 100ms). Bạn đang bắt đầu phát âm gần như đồng thời, "
                    f"dẫn đến việc cơ quan thính giác bị nhiễu và không nghe trọn vẹn được sắc thái bản ngữ."
                ),
                "practice_tip": "Hãy giữ độ trễ tối ưu 150–400ms (khoảng 1/4 nhịp mora). Để tai nghe từ đầu tiên trước khi miệng cất lời.",
            }

        if rating == "trailing":
            return {
                "title": "Bị tụt nhịp Shadowing (Trailing)",
                "category": "Độ trễ Shadowing",
                "explanation": (
                    f"Độ trễ phản xạ đạt {lag_ms:.0f}ms (> 700ms). Bạn đang rơi vào thói quen nghe hết câu rồi mới lặp lại (Repeat) "
                    f"thay vì duy trì phản xạ đuổi bóng (Shadowing) tức thì."
                ),
                "practice_tip": "Nói đuổi sát theo giọng mẫu hơn, phát âm ngay khi người nói vừa dứt âm tiết đầu tiên.",
            }

        if rating == "hesitant":
            return {
                "title": "Độ trễ Shadowing hơi chậm",
                "category": "Độ trễ Shadowing",
                "explanation": f"Độ trễ phản xạ đạt {lag_ms:.0f}ms. Bạn bám sát nội dung tốt nhưng nhịp đuổi bóng còn hơi dè dặt.",
                "practice_tip": "Thả lỏng cơ hàm và tự tin bật âm sớm hơn để đưa độ trễ về vùng vàng 250ms.",
            }

        return None

    @classmethod
    def estimate_acoustic_lag(
        cls,
        user_samples: np.ndarray,
        reference_samples: np.ndarray,
        sample_rate: int = 16000,
        max_search_lag_ms: float = 1500.0,
    ) -> tuple[float, float, str]:
        """Estimates actual auditory-vocal shadowing lag (ms) between user audio and model audio.

        Combines Generalized Cross-Correlation with Phase Transform (GCC-PHAT) and Energy Envelope Cross-Correlation.
        Returns: (lag_ms, confidence [0.0, 1.0], classification)
        """
        if len(user_samples) < int(sample_rate * 0.1) or len(reference_samples) < int(sample_rate * 0.1):
            return cls.SWEET_SPOT_MS, 0.3, "optimal"

        # 1. Compute RMS energy envelopes (10ms hop, 20ms window) for speech activity matching
        hop_samples = int(sample_rate * 0.010)
        win_samples = int(sample_rate * 0.020)

        user_env = cls._compute_rms_envelope(user_samples, win_samples, hop_samples)
        ref_env = cls._compute_rms_envelope(reference_samples, win_samples, hop_samples)

        if len(user_env) < 5 or len(ref_env) < 5:
            return cls.SWEET_SPOT_MS, 0.3, "optimal"

        # 2. Envelope cross-correlation
        max_lag_frames = int((max_search_lag_ms / 1000.0) / 0.010)
        best_lag_frames, env_corr_val = cls._envelope_correlation_peak(user_env, ref_env, max_lag_frames)
        lag_ms_env = float(best_lag_frames * 10.0)

        # 3. GCC-PHAT for fine acoustic resolution (up to 4000 samples / 250ms range)
        gcc_lag_ms, gcc_conf = cls._gcc_phat_peak(user_samples, reference_samples, sample_rate, max_search_lag_ms)

        # If GCC-PHAT has high confidence and is within reasonable envelope range, blend them
        if gcc_conf >= 0.4 and abs(gcc_lag_ms - lag_ms_env) < 300.0:
            final_lag_ms = round(0.70 * gcc_lag_ms + 0.30 * lag_ms_env, 1)
            confidence = round(min(0.98, 0.60 * gcc_conf + 0.40 * env_corr_val), 2)
        else:
            final_lag_ms = round(lag_ms_env, 1)
            confidence = round(min(0.95, env_corr_val), 2)

        final_lag_ms = max(0.0, min(max_search_lag_ms, final_lag_ms))
        classification = cls.classify_lag(final_lag_ms)
        return final_lag_ms, confidence, classification

    @classmethod
    def _compute_rms_envelope(cls, signal: np.ndarray, win: int, hop: int) -> np.ndarray:
        """Computes frame-wise RMS energy envelope."""
        n_frames = max(1, (len(signal) - win) // hop)
        envelope = np.zeros(n_frames, dtype=np.float64)
        for i in range(n_frames):
            frame = signal[i * hop : i * hop + win]
            envelope[i] = float(np.sqrt(np.mean(frame**2))) if len(frame) > 0 else 0.0
        # Normalize envelope
        max_val = np.max(envelope) if len(envelope) > 0 else 0.0
        if max_val > 1e-6:
            envelope /= max_val
        return envelope

    @classmethod
    def _envelope_correlation_peak(
        cls,
        user_env: np.ndarray,
        ref_env: np.ndarray,
        max_lag_frames: int,
    ) -> tuple[int, float]:
        """Finds lag tau >= 0 where user_env correlates maximally with delayed ref_env."""
        # We search positive lag: user speaks AFTER reference (shadowing lag)
        user_norm = user_env - np.mean(user_env)
        ref_norm = ref_env - np.mean(ref_env)

        std_u = np.std(user_norm)
        std_r = np.std(ref_norm)
        if std_u < 1e-6 or std_r < 1e-6:
            return 25, 0.4  # Default 25 frames = 250ms

        corr = np.correlate(user_norm, ref_norm, mode="full")
        # Midpoint is where user and ref align at lag 0
        mid = len(ref_norm) - 1
        search_region = corr[mid : mid + min(max_lag_frames + 1, len(corr) - mid)]

        if len(search_region) == 0:
            return 25, 0.4

        best_idx = int(np.argmax(search_region))
        norm_factor = (std_u * std_r * len(user_norm)) + 1e-8
        corr_coef = float(search_region[best_idx] / norm_factor)
        return best_idx, max(0.1, min(1.0, corr_coef))

    @classmethod
    def _gcc_phat_peak(
        cls,
        user_sig: np.ndarray,
        ref_sig: np.ndarray,
        sr: int,
        max_lag_ms: float,
    ) -> tuple[float, float]:
        """Generalized Cross-Correlation with Phase Transform (GCC-PHAT)."""
        # Trim to common length for FFT (up to 5 seconds)
        n_samples = min(len(user_sig), len(ref_sig), sr * 5)
        u = user_sig[:n_samples].astype(np.float64)
        r = ref_sig[:n_samples].astype(np.float64)

        fft_len = int(2 ** np.ceil(np.log2(2 * n_samples - 1)))
        U = np.fft.rfft(u, n=fft_len)
        R = np.fft.rfft(r, n=fft_len)

        # Cross power spectrum with phase whitening
        R_cross = U * np.conj(R)
        denom = np.abs(R_cross) + 1e-8
        cc = np.fft.irfft(R_cross / denom, n=fft_len)

        # Search positive lags corresponding to [0, max_lag_ms]
        max_lag_samples = int((max_lag_ms / 1000.0) * sr)
        search_window = cc[: min(max_lag_samples + 1, len(cc))]

        if len(search_window) == 0:
            return cls.SWEET_SPOT_MS, 0.3

        peak_idx = int(np.argmax(search_window))
        peak_val = float(search_window[peak_idx])

        lag_ms = (peak_idx / float(sr)) * 1000.0
        # Confidence derived from peak prominence
        mean_val = float(np.mean(search_window))
        prominence = max(0.0, peak_val - mean_val)
        conf = min(0.95, prominence * 8.0)
        return lag_ms, conf
