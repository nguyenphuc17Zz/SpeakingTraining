import math
from typing import Any

import numpy as np

from app.domains.pronunciation.contracts import PitchCurve, PitchPoint


class PitchExtractor:
    """SOTA Fundamental Frequency (F0) Contour Extractor based on pYIN (Probabilistic YIN) and Viterbi HMM Smoothing.

    References:
      - De Cheveigné, A., & Kawahara, H. (2002). YIN, a fundamental frequency estimator for speech and music. JASA.
      - Mauch, M., & Dixon, S. (2014). pYIN: A fundamental frequency estimator using probabilistic YIN and HMM. ICASSP.
    """

    F0_MIN = 60.0    # Hz (low male pitch limit)
    F0_MAX = 450.0   # Hz (high female/child pitch limit)
    FRAME_MS = 25    # 25ms frame window
    HOP_MS = 10      # 10ms hop interval
    YIN_THRESHOLD = 0.15  # Dip threshold for Cumulative Mean Normalized Difference Function

    @classmethod
    def extract_f0(cls, samples: np.ndarray, sample_rate: int = 16000) -> PitchCurve:
        """Extracts F0 contour using pYIN (Cumulative Mean Normalized Difference Function) with Viterbi path smoothing.

        Performs speaker normalization into semitones relative to speaker's median F0.
        """
        if len(samples) < int(sample_rate * 0.05):
            return PitchCurve(points=[], confidence=0.0)

        frame_len = int(sample_rate * (cls.FRAME_MS / 1000.0))
        hop_len = int(sample_rate * (cls.HOP_MS / 1000.0))
        num_frames = max(1, (len(samples) - frame_len) // hop_len)

        min_lag = max(2, int(sample_rate / cls.F0_MAX))
        max_lag = min(frame_len - 1, int(sample_rate / cls.F0_MIN))

        # 1. Per-frame YIN candidate extraction
        frame_candidates: list[list[tuple[float, float]]] = []  # [(f0, prob)]
        timestamps_ms: list[int] = []

        for f in range(num_frames):
            start = f * hop_len
            frame = samples[start : start + frame_len]
            t_ms = int((start / float(sample_rate)) * 1000)
            timestamps_ms.append(t_ms)

            # Energy / RMS check
            rms = float(np.sqrt(np.mean(frame**2))) if len(frame) > 0 else 0.0
            if rms < 0.005:
                # Definite unvoiced (silence/near-silence)
                frame_candidates.append([(0.0, 1.0)])
                continue

            # Compute YIN CMNDF and candidates
            cands = cls._extract_yin_candidates(frame, sample_rate, min_lag, max_lag)
            frame_candidates.append(cands)

        # 2. Viterbi Dynamic Programming smoothing across frames
        smoothed_f0_list, confidences = cls._viterbi_smooth(frame_candidates)

        # 3. Collect voiced values for speaker median semitone calculation
        voiced_f0_values = [f for f in smoothed_f0_list if f > cls.F0_MIN]

        if not voiced_f0_values:
            return PitchCurve(
                points=[
                    PitchPoint(
                        timestamp_ms=timestamps_ms[i],
                        frequency_hz=0.0,
                        normalized_semitones=0.0,
                        is_voiced=False,
                        confidence=confidences[i],
                    )
                    for i in range(len(timestamps_ms))
                ],
                speaker_f0_mean=None,
                speaker_f0_std=None,
                voiced_ratio=0.0,
                confidence=0.3,
            )

        # 4. Compute speaker median baseline
        f0_array = np.array(voiced_f0_values)
        median_f0 = float(np.median(f0_array))
        mean_f0 = float(np.mean(f0_array))
        std_f0 = float(np.std(f0_array)) if len(f0_array) > 1 else 10.0

        # 5. Construct PitchPoint list with speaker-normalized relative semitones
        pitch_points: list[PitchPoint] = []
        for i, f0 in enumerate(smoothed_f0_list):
            is_voiced = bool(f0 >= cls.F0_MIN)
            if is_voiced and median_f0 > 0:
                semitones = 12.0 * math.log2(f0 / median_f0)
            else:
                semitones = 0.0

            pitch_points.append(
                PitchPoint(
                    timestamp_ms=timestamps_ms[i],
                    frequency_hz=round(f0, 1),
                    normalized_semitones=round(semitones, 2),
                    is_voiced=is_voiced,
                    confidence=round(confidences[i], 3),
                )
            )

        voiced_ratio = len(voiced_f0_values) / float(len(smoothed_f0_list)) if smoothed_f0_list else 0.0
        overall_conf = 0.95 if voiced_ratio > 0.25 else 0.55

        return PitchCurve(
            points=pitch_points,
            speaker_f0_mean=round(mean_f0, 1),
            speaker_f0_std=round(std_f0, 1),
            voiced_ratio=round(voiced_ratio, 3),
            confidence=overall_conf,
            normalization_method="semitone_median_relative_pyin",
        )

    @classmethod
    def _extract_yin_candidates(
        cls,
        frame: np.ndarray,
        sr: int,
        min_lag: int,
        max_lag: int,
    ) -> list[tuple[float, float]]:
        """Computes Cumulative Mean Normalized Difference Function (CMNDF) and extracts candidate pitches with probabilities."""
        w = len(frame) // 2
        if w < max_lag:
            w = len(frame) - max_lag

        # Difference function d(tau)
        # d_t(tau) = sum_{j=0}^{W-1} (x_j - x_{j+tau})^2
        diff = np.zeros(max_lag + 1, dtype=np.float64)
        x = frame.astype(np.float64)

        for tau in range(1, max_lag + 1):
            delta = x[:w] - x[tau : tau + w]
            diff[tau] = np.sum(delta**2)

        # Cumulative Mean Normalized Difference Function (CMNDF)
        # cmndf[0] = 1; cmndf[tau] = diff[tau] / ((1/tau) * sum_{j=1}^tau diff[j])
        cmndf = np.ones(max_lag + 1, dtype=np.float64)
        cum_sum = 0.0
        for tau in range(1, max_lag + 1):
            cum_sum += diff[tau]
            if cum_sum > 1e-8:
                cmndf[tau] = diff[tau] / (cum_sum / tau)
            else:
                cmndf[tau] = 1.0

        candidates: list[tuple[float, float]] = []

        # Find local minima below YIN_THRESHOLD or first dip
        first_below = None
        for tau in range(min_lag, max_lag):
            if cmndf[tau] < cls.YIN_THRESHOLD:
                if cmndf[tau] <= cmndf[tau - 1] and cmndf[tau] <= cmndf[tau + 1]:
                    first_below = tau
                    break

        if first_below is not None:
            # Parabolic interpolation around minimum
            exact_tau = cls._parabolic_interpolation(cmndf, first_below)
            if exact_tau > 0:
                f0 = sr / exact_tau
                if cls.F0_MIN <= f0 <= cls.F0_MAX:
                    prob = max(0.2, min(0.99, 1.0 - cmndf[first_below]))
                    candidates.append((f0, prob))

        # If no dip below threshold, check global minimum in range
        if not candidates:
            search_region = cmndf[min_lag : max_lag + 1]
            if len(search_region) > 0:
                best_idx = int(np.argmin(search_region)) + min_lag
                best_val = cmndf[best_idx]
                if best_val < 0.45:
                    exact_tau = cls._parabolic_interpolation(cmndf, best_idx)
                    f0 = sr / exact_tau if exact_tau > 0 else 0.0
                    if cls.F0_MIN <= f0 <= cls.F0_MAX:
                        candidates.append((f0, max(0.1, 1.0 - best_val)))

        # Always include unvoiced (0 Hz) candidate
        voiced_prob = max((c[1] for c in candidates), default=0.0)
        unvoiced_prob = max(0.05, 1.0 - voiced_prob)
        candidates.append((0.0, unvoiced_prob))

        return candidates

    @staticmethod
    def _parabolic_interpolation(array: np.ndarray, x: int) -> float:
        """Finds sub-sample minimum position via 3-point parabolic interpolation."""
        if x <= 0 or x >= len(array) - 1:
            return float(x)
        alpha = array[x - 1]
        beta = array[x]
        gamma = array[x + 1]
        denom = 2.0 * (alpha - 2.0 * beta + gamma)
        if abs(denom) > 1e-6:
            delta = (alpha - gamma) / denom
            return float(x + delta)
        return float(x)

    @classmethod
    def _viterbi_smooth(
        cls,
        frame_candidates: list[list[tuple[float, float]]],
    ) -> tuple[list[float], list[float]]:
        """Finds globally optimal pitch sequence across frames minimizing pitch jumps and octave errors."""
        n_frames = len(frame_candidates)
        if n_frames == 0:
            return [], []

        # dp[frame_idx][cand_idx] = lowest cost
        dp: list[list[float]] = []
        backpointer: list[list[int]] = []

        # Initialize first frame
        first_cands = frame_candidates[0]
        dp.append([-math.log(max(1e-4, c[1])) for c in first_cands])
        backpointer.append([-1] * len(first_cands))

        for f in range(1, n_frames):
            prev_cands = frame_candidates[f - 1]
            curr_cands = frame_candidates[f]

            curr_dp: list[float] = []
            curr_bp: list[int] = []

            for curr_f0, curr_prob in curr_cands:
                emission_cost = -math.log(max(1e-4, curr_prob))
                best_cost = float("inf")
                best_prev_idx = 0

                for p_idx, (prev_f0, _) in enumerate(prev_cands):
                    # Transition cost
                    trans_cost = cls._transition_cost(prev_f0, curr_f0)
                    total = dp[f - 1][p_idx] + trans_cost + emission_cost

                    if total < best_cost:
                        best_cost = total
                        best_prev_idx = p_idx

                curr_dp.append(best_cost)
                curr_bp.append(best_prev_idx)

            dp.append(curr_dp)
            backpointer.append(curr_bp)

        # Traceback
        best_cand_idx = int(np.argmin(dp[-1]))
        smoothed_f0: list[float] = []
        confidences: list[float] = []

        for f in range(n_frames - 1, -1, -1):
            f0_val, conf = frame_candidates[f][best_cand_idx]
            smoothed_f0.append(f0_val)
            confidences.append(conf)
            best_cand_idx = backpointer[f][best_cand_idx]

        smoothed_f0.reverse()
        confidences.reverse()
        return smoothed_f0, confidences

    @classmethod
    def _transition_cost(cls, f1: float, f2: float) -> float:
        """Computes transition penalty between adjacent frames.

        Heavy penalty for pitch jumps > 3 semitones between voiced frames.
        Moderate penalty for voiced/unvoiced boundary.
        Zero penalty for continuous unvoiced.
        """
        v1 = bool(f1 >= cls.F0_MIN)
        v2 = bool(f2 >= cls.F0_MIN)

        if not v1 and not v2:
            return 0.0  # Unvoiced -> Unvoiced: free
        if (not v1 and v2) or (v1 and not v2):
            return 1.2  # Voicing state boundary

        # Both voiced: semitone difference penalty
        semitone_diff = abs(12.0 * math.log2(f2 / f1))
        if semitone_diff <= 1.5:
            return 0.1 * semitone_diff
        elif semitone_diff <= 3.5:
            return 0.8 * semitone_diff
        else:
            # Huge penalty for jumps > 3.5 semitones (octave doubling/halving error prevention)
            return 4.0 + 2.0 * semitone_diff
