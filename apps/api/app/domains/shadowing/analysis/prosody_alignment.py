from __future__ import annotations

import math
from typing import Sequence
import numpy as np
from pydantic import BaseModel, Field


class HesitationSegment(BaseModel):
    start_time_ms: int
    end_time_ms: int
    duration_ms: int
    severity: str  # "minor", "moderate", "severe"
    reason: str


class ProsodyAlignmentResultDTO(BaseModel):
    warping_distance: float
    tempo_consistency_score: float
    mean_local_lag_ms: float
    max_local_lag_ms: float
    hesitation_segments: list[HesitationSegment] = Field(default_factory=list)
    alignment_path_length: int
    reference_frames: int
    learner_frames: int
    status: str = "success"


class ProsodyDynamicTimeWarper:
    """Constrained Dynamic Time Warping (DTW) with Sakoe-Chiba Band for Prosody & Tempo Alignment.

    Mathematical Foundation:
    - Sakoe & Chiba (1978): Dynamic programming algorithm optimization for spoken word recognition.
    - Salvador & Chan (2007): FastDTW: Toward accurate dynamic time warping in linear time and space.
    - Compares non-linear time variations between reference audio and learner speech, isolating
      momentary hesitations, rushed segments, and tempo stability.
    """

    @classmethod
    def align(
        cls,
        reference_series: Sequence[float],
        learner_series: Sequence[float],
        frame_step_ms: int = 20,
        band_radius: int | None = None,
        band_radius_ratio: float = 0.20,
    ) -> ProsodyAlignmentResultDTO:
        """Performs Sakoe-Chiba constrained DTW alignment between reference and learner prosody contours.

        Args:
            reference_series: 1D array of reference prosody values (e.g. F0 or energy envelope).
            learner_series: 1D array of learner prosody values.
            frame_step_ms: Duration of each analysis frame in milliseconds (default 20ms).
            band_radius: Sakoe-Chiba band radius (in frames). If None, computed from ratio.
            band_radius_ratio: Ratio of series length to determine band width.
        """
        N = len(reference_series)
        M = len(learner_series)

        if N == 0 or M == 0:
            return ProsodyAlignmentResultDTO(
                warping_distance=0.0,
                tempo_consistency_score=0.0,
                mean_local_lag_ms=0.0,
                max_local_lag_ms=0.0,
                alignment_path_length=0,
                reference_frames=N,
                learner_frames=M,
                status="insufficient_data",
            )

        # Compute Sakoe-Chiba window radius R
        if band_radius is None:
            band_radius = max(5, int(max(N, M) * band_radius_ratio))

        # Normalize series to zero mean and unit variance if variance > 0
        ref_arr = np.array(reference_series, dtype=np.float64)
        lrn_arr = np.array(learner_series, dtype=np.float64)

        if np.std(ref_arr) > 1e-6:
            ref_arr = (ref_arr - np.mean(ref_arr)) / np.std(ref_arr)
        if np.std(lrn_arr) > 1e-6:
            lrn_arr = (lrn_arr - np.mean(lrn_arr)) / np.std(lrn_arr)

        slope = float(N) / float(M)

        INF = float("inf")
        cost = np.full((N, M), INF, dtype=np.float64)

        cost[0, 0] = float((ref_arr[0] - lrn_arr[0]) ** 2)

        for i in range(N):
            center_j = int(i / slope)
            j_min = max(0, center_j - band_radius)
            j_max = min(M, center_j + band_radius + 1)

            for j in range(j_min, j_max):
                if i == 0 and j == 0:
                    continue

                dist = float((ref_arr[i] - lrn_arr[j]) ** 2)

                c1 = cost[i - 1, j] if i > 0 else INF
                c2 = cost[i, j - 1] if j > 0 else INF
                c3 = cost[i - 1, j - 1] if (i > 0 and j > 0) else INF

                min_prev = min(c1, c2, c3)
                if min_prev != INF:
                    cost[i, j] = dist + min_prev

        if cost[N - 1, M - 1] == INF:
            # Band was too narrow; fallback with unconstrained band
            return cls.align(
                reference_series=reference_series,
                learner_series=learner_series,
                frame_step_ms=frame_step_ms,
                band_radius=max(N, M),
            )

        # Backtrack optimal path
        path: list[tuple[int, int]] = []
        curr_i = N - 1
        curr_j = M - 1
        path.append((curr_i, curr_j))

        while curr_i > 0 or curr_j > 0:
            c1 = cost[curr_i - 1, curr_j] if curr_i > 0 else INF
            c2 = cost[curr_i, curr_j - 1] if curr_j > 0 else INF
            c3 = cost[curr_i - 1, curr_j - 1] if (curr_i > 0 and curr_j > 0) else INF

            min_val = min(c1, c2, c3)
            if curr_i > 0 and curr_j > 0 and c3 == min_val:
                curr_i -= 1
                curr_j -= 1
            elif curr_i > 0 and c1 == min_val:
                curr_i -= 1
            elif curr_j > 0 and c2 == min_val:
                curr_j -= 1
            else:
                break
            path.append((curr_i, curr_j))

        path.reverse()
        path_len = len(path)
        normalized_distance = float(cost[N - 1, M - 1] / max(1, path_len))

        # Local temporal deviations (lag at each reference frame)
        ref_to_lrn: dict[int, list[int]] = {}
        for i_frame, j_frame in path:
            if i_frame not in ref_to_lrn:
                ref_to_lrn[i_frame] = []
            ref_to_lrn[i_frame].append(j_frame)

        local_lags_ms: list[float] = []
        for i_frame in range(N):
            if i_frame in ref_to_lrn:
                matched_j = float(np.mean(ref_to_lrn[i_frame]))
                lag_ms = (matched_j - i_frame) * frame_step_ms
                local_lags_ms.append(lag_ms)

        mean_lag = float(np.mean(local_lags_ms)) if local_lags_ms else 0.0
        max_lag = float(np.max(np.abs(local_lags_ms))) if local_lags_ms else 0.0

        # Tempo consistency score
        std_lag = float(np.std(local_lags_ms)) if local_lags_ms else 0.0
        tempo_consistency = float(np.clip(100.0 * math.exp(-(std_lag**2) / (2.0 * (150.0**2))), 10.0, 100.0))

        # Detect hesitation segments where learner stalled
        hesitation_segments: list[HesitationSegment] = []
        consec_ref_repeats = 0
        seg_start_ms = 0

        for idx in range(1, len(path)):
            prev_i, prev_j = path[idx - 1]
            curr_i, curr_j = path[idx]

            if curr_j == prev_j and curr_i > prev_i:
                if consec_ref_repeats == 0:
                    seg_start_ms = prev_i * frame_step_ms
                consec_ref_repeats += 1
            else:
                if consec_ref_repeats >= 4:  # >= 80ms stall
                    dur_ms = consec_ref_repeats * frame_step_ms
                    sev = "severe" if dur_ms >= 300 else ("moderate" if dur_ms >= 160 else "minor")
                    hesitation_segments.append(
                        HesitationSegment(
                            start_time_ms=seg_start_ms,
                            end_time_ms=seg_start_ms + dur_ms,
                            duration_ms=dur_ms,
                            severity=sev,
                            reason=f"Phát hiện ngập ngừng / trễ nhịp tại {seg_start_ms}ms (kéo dài {dur_ms}ms).",
                        )
                    )
                consec_ref_repeats = 0

        return ProsodyAlignmentResultDTO(
            warping_distance=round(normalized_distance, 3),
            tempo_consistency_score=round(tempo_consistency, 1),
            mean_local_lag_ms=round(mean_lag, 1),
            max_local_lag_ms=round(max_lag, 1),
            hesitation_segments=hesitation_segments,
            alignment_path_length=path_len,
            reference_frames=N,
            learner_frames=M,
            status="success",
        )
