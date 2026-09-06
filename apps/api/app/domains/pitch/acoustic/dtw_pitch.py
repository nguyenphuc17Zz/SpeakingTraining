"""
DTWPitchEngine — World SOTA Dynamic Time Warping with Semitone Normalization
for Tokyo Japanese Pitch Accent Alignment and Assessment.

References:
  - NHK Japanese Pronunciation and Accent Dictionary (NHK日本語発音アクセント新辞典).
  - Vance, T. J. (2008). The Sounds of Japanese. Cambridge University Press.
  - Sakoe, H., & Chiba, S. (1978). Dynamic programming algorithm optimization for
    spoken word recognition. IEEE Transactions on ASSP.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class DTWContourResult:
    similarity_score: float
    normalized_distance: float
    path_length: int
    alignment_summary: str


class DTWPitchEngine:
    """
    Computes speaker-independent pitch contour similarity via Dynamic Time Warping
    operating over semitone-normalized mora intervals.
    """

    # Minor third musical interval (~3.0 semitones) standard in Tokyo pitch drop
    HIGH_MORA_SEMITONE: float = 1.5
    LOW_MORA_SEMITONE: float = -1.5

    @classmethod
    def hz_to_semitones(cls, f0_values: list[float], median_f0: float | None = None) -> list[float]:
        """
        Converts fundamental frequency in Hz to relative semitones centered on median pitch.
        st = 12 * log2(f0 / median_f0)
        """
        valid_f0 = [f for f in f0_values if f and f > 30.0]
        if not valid_f0:
            return [0.0] * len(f0_values)

        if median_f0 is None or median_f0 <= 30.0:
            sorted_f0 = sorted(valid_f0)
            median_f0 = sorted_f0[len(sorted_f0) // 2]

        semitones: list[float] = []
        for f in f0_values:
            if f and f > 30.0:
                st = 12.0 * math.log2(f / median_f0)
                semitones.append(round(st, 3))
            else:
                semitones.append(0.0)
        return semitones

    @classmethod
    def pattern_to_canonical_semitones(cls, pattern: list[str]) -> list[float]:
        """
        Maps discrete H/L Tokyo accent patterns (e.g. ['L', 'H', 'H', 'L'])
        into reference semitone values.
        """
        result: list[float] = []
        for p in pattern:
            if p.upper() == "H":
                result.append(cls.HIGH_MORA_SEMITONE)
            else:
                result.append(cls.LOW_MORA_SEMITONE)
        return result

    @classmethod
    def compute_dtw_distance(
        cls,
        seq_a: list[float],
        seq_b: list[float],
    ) -> tuple[float, int]:
        """
        Computes the normalized Dynamic Time Warping distance between two 1D numerical sequences.
        Returns (normalized_distance, path_length).
        """
        n = len(seq_a)
        m = len(seq_b)

        if n == 0 or m == 0:
            return (10.0, max(n, m, 1))

        # Initialize DP matrix with infinity
        dp = [[float("inf")] * m for _ in range(n)]

        # Base case
        dp[0][0] = abs(seq_a[0] - seq_b[0])

        # First column
        for i in range(1, n):
            dp[i][0] = dp[i - 1][0] + abs(seq_a[i] - seq_b[0])

        # First row
        for j in range(1, m):
            dp[0][j] = dp[0][j - 1] + abs(seq_a[0] - seq_b[j])

        # DP recurrence
        for i in range(1, n):
            for j in range(1, m):
                cost = abs(seq_a[i] - seq_b[j])
                dp[i][j] = cost + min(
                    dp[i - 1][j],      # Insertion
                    dp[i][j - 1],      # Deletion
                    dp[i - 1][j - 1],  # Match
                )

        total_cost = dp[n - 1][m - 1]
        path_length = n + m
        normalized_distance = total_cost / float(path_length)

        return (normalized_distance, path_length)

    @classmethod
    def compute_pitch_contour_similarity(
        cls,
        observed_mora_semitones: list[float],
        expected_pattern: list[str],
        canonical_semitones: list[float] | None = None,
    ) -> DTWContourResult:
        """
        Aligns observed user mora pitch with canonical Tokyo accent pattern using DTW.
        Produces scientific similarity score in [0.0, 100.0].
        """
        if not observed_mora_semitones or not expected_pattern:
            return DTWContourResult(
                similarity_score=70.0,
                normalized_distance=1.0,
                path_length=1,
                alignment_summary="Insufficient contour data for DTW",
            )

        ref_semitones = canonical_semitones or cls.pattern_to_canonical_semitones(expected_pattern)

        # Normalize observed semitones so mean is centered around 0
        mean_obs = sum(observed_mora_semitones) / len(observed_mora_semitones)
        centered_obs = [round(v - mean_obs, 3) for v in observed_mora_semitones]

        distance, path_len = cls.compute_dtw_distance(centered_obs, ref_semitones)

        # Exponential decay mapping:
        # Distance = 0.0 st  -> 100%
        # Distance = 0.5 st  -> ~80%
        # Distance = 1.0 st  -> ~64%
        # Distance = 1.6 st  -> ~49% (inverted pattern)
        # Distance = 3.0 st  -> ~26%
        decay_factor = 0.45
        raw_score = 100.0 * math.exp(-decay_factor * distance)
        similarity_score = max(10.0, min(100.0, round(raw_score, 1)))

        summary = f"DTW Normalized Distance: {distance:.2f} semitones (Score: {similarity_score:.1f}%)"

        return DTWContourResult(
            similarity_score=similarity_score,
            normalized_distance=round(distance, 3),
            path_length=path_len,
            alignment_summary=summary,
        )
