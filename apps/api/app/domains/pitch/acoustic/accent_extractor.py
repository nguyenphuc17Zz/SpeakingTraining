"""AccentPatternExtractor — mora-level H/L + downstep detection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from app.domains.pronunciation.contracts import PitchCurve


@dataclass
class AccentPatternResult:
    mora_values: list[str]  # ["L","H","H","L"]
    drop_location: int | None
    rise_location: int | None
    confidence: float


class AccentPatternExtractor:
    def extract(self, pitch_curve: PitchCurve, mora_boundaries: list[Any]) -> AccentPatternResult:
        if not pitch_curve.points or not mora_boundaries:
            return AccentPatternResult(mora_values=[], drop_location=None, rise_location=None, confidence=0.2)

        # Aggregate normalized semitone per mora window
        mora_vals: list[float] = []
        for b in mora_boundaries:
            # Collect points within mora window
            pts = [p for p in pitch_curve.points if b.start_ms <= p.timestamp_ms < b.end_ms and p.is_voiced]
            if not pts:
                # No voiced points, use interpolated or 0
                mora_vals.append(0.0)
            else:
                # Mean semitone
                mora_vals.append(float(np.mean([p.normalized_semitones for p in pts])))

        if not mora_vals:
            return AccentPatternResult(mora_values=[], drop_location=None, rise_location=None, confidence=0.2)

        # Classify H/L per mora via median split + thresholds
        # Use robust threshold: high if > 0.5 semitone above median? Actually median is 0, so >0.8 => H
        # Simplified: if mora_val > 0.5 => H else L, but need at least one H
        # Use local slope
        pattern: list[str] = []
        for v in mora_vals:
            pattern.append("H" if v > 0.5 else "L" if v < -0.3 else ("H" if v > 0 else "L"))

        # Ensure at least one H for heiban etc.
        if all(p == "L" for p in pattern) and mora_vals:
            # Max is H
            idx = int(np.argmax(mora_vals))
            pattern[idx] = "H"

        # Drop detection: H -> L transition where drop >1.2 semitone
        drop = None
        for i in range(1, len(mora_vals)):
            if pattern[i-1] == "H" and pattern[i] == "L" and (mora_vals[i-1] - mora_vals[i]) > 1.0:
                drop = i + 1  # 1-indexed mora position
                break
            # Also detect large fall even if pattern still H/L borderline
            if mora_vals[i-1] - mora_vals[i] > 1.5 and drop is None:
                drop = i + 1

        # Rise location: L->H
        rise = None
        for i in range(1, len(pattern)):
            if pattern[i-1] == "L" and pattern[i] == "H":
                rise = i + 1
                break

        # Confidence based on voiced ratio and mora coverage
        voiced_ratio = pitch_curve.voiced_ratio
        conf = 0.92 if voiced_ratio > 0.4 else 0.75 if voiced_ratio > 0.25 else 0.5
        if len([v for v in mora_vals if abs(v) < 0.1]) > len(mora_vals) * 0.6:
            conf = min(conf, 0.6)  # flat contour

        return AccentPatternResult(mora_values=pattern, drop_location=drop, rise_location=rise, confidence=conf)
