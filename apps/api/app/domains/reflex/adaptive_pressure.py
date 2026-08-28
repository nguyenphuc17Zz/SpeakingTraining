"""Adaptive pressure — deterministic logic for timer difficulty adaptation.

Rules per spec #32-33:
- accuracy high + reaction fast + confidence high → slightly increase pressure (harder = smaller timer)
- accuracy low OR context low → decrease pressure / simplify task
- accuracy high BUT reaction slow → keep difficulty, focus automaticity
- reaction fast BUT accuracy low → do NOT reward speed, reduce pressure

Requires minimum 5-10 comparable attempts (same sub_mode + similar timer).
"""

from __future__ import annotations

from typing import Any

from app.domains.reflex.pressure_profiles import ADAPTIVE_PRESSURE_ORDER, timer_for_level


def _filter_comparable(attempts: list[dict[str, Any]], sub_mode: str | None) -> list[dict[str, Any]]:
    if not sub_mode:
        return attempts
    return [a for a in attempts if a.get("sub_mode") == sub_mode or a.get("exercise_type") == sub_mode]


def recommend_next_pressure(
    current_level: str,
    recent_attempts: list[dict[str, Any]],
    *,
    sub_mode: str | None = None,
    min_samples: int = 5,
) -> tuple[str, str]:
    """Returns (next_level, reason).

    recent_attempts: list of {success, score, reaction_latency_ms, timer_limit_ms, confidence, sub_mode}
    """
    comparable = _filter_comparable(recent_attempts, sub_mode)
    if len(comparable) < min_samples:
        return current_level, f"Insufficient comparable attempts ({len(comparable)}/{min_samples}) — keep current"

    # Aggregate last min_samples
    window = comparable[-min_samples:]
    successes = sum(1 for a in window if a.get("success"))
    avg_score = sum(float(a.get("score", 0)) for a in window) / len(window)
    # Reaction relative to timer
    latencies = [a.get("reaction_latency_ms") for a in window if a.get("reaction_latency_ms") is not None]
    avg_latency = sum(latencies) / len(latencies) if latencies else None
    avg_timer = sum(float(a.get("timer_limit_ms", 3000)) for a in window) / len(window)
    # Confidence
    avg_conf = sum(float(a.get("confidence", 0.7)) for a in window) / len(window)

    accuracy_high = successes / len(window) >= 0.80 and avg_score >= 75
    reaction_fast = avg_latency is not None and avg_latency / avg_timer < 0.65 if avg_timer else False
    confidence_high = avg_conf >= 0.75
    accuracy_low = successes / len(window) < 0.55 or avg_score < 55

    if accuracy_high and reaction_fast and confidence_high:
        # Increase pressure slightly (harder)
        try:
            idx = ADAPTIVE_PRESSURE_ORDER.index(current_level)
        except ValueError:
            idx = 1
        if idx < len(ADAPTIVE_PRESSURE_ORDER) - 1:
            next_level = ADAPTIVE_PRESSURE_ORDER[idx + 1]
            return next_level, f"Accuracy high ({successes}/{len(window)}, avg {avg_score:.0f}) + reaction fast ({avg_latency:.0f}ms) → increase pressure"
        return current_level, "Already at hardest level"

    if accuracy_low:
        try:
            idx = ADAPTIVE_PRESSURE_ORDER.index(current_level)
        except ValueError:
            idx = 1
        if idx > 0:
            next_level = ADAPTIVE_PRESSURE_ORDER[idx - 1]
            return next_level, f"Accuracy low ({successes}/{len(window)}, avg {avg_score:.0f}) → decrease pressure"
        return current_level, "Already at easiest level"

    # Accuracy high but reaction slow → keep, focus automaticity
    if accuracy_high and not reaction_fast:
        return current_level, f"Accuracy high but reaction slow ({avg_latency:.0f}ms vs {avg_timer:.0f}ms) → keep pressure, focus automaticity"

    # Fast but inaccurate → reduce pressure (do not reward speed)
    if reaction_fast and accuracy_low:
        try:
            idx = ADAPTIVE_PRESSURE_ORDER.index(current_level)
        except ValueError:
            idx = 1
        if idx > 0:
            return ADAPTIVE_PRESSURE_ORDER[idx - 1], "Fast but inaccurate → reduce pressure, reinforce correctness"
        return current_level, "Fast but inaccurate but already easiest"

    return current_level, "Stable — keep current pressure"


def estimate_pressure_threshold(attempts: list[dict[str, Any]], min_accuracy: float = 0.75) -> dict[str, Any] | None:
    """Derives personal pressure threshold: max pressure (smallest timer) where accuracy stays above min.

    Returns {threshold_level, threshold_ms, stable_until_ms, comfort_window}
    """
    if len(attempts) < 8:
        return None
    # Group by timer level
    from collections import defaultdict
    buckets: dict[int, list[dict]] = defaultdict(list)
    for a in attempts:
        tl = int(a.get("timer_limit_ms", 0))
        if tl:
            # Round to profile values
            buckets[tl].append(a)
    # Sort by timer asc (hardest first)
    sorted_timers = sorted(buckets.keys())
    stable_until = None
    for tl in sorted_timers:
        bucket = buckets[tl]
        if len(bucket) < 3:
            continue
        acc = sum(1 for x in bucket if x.get("success")) / len(bucket)
        if acc >= min_accuracy:
            stable_until = tl
        else:
            break
    if stable_until is None:
        # Use hardest stable
        return None
    # Find comfort window: stable_until + one easier tier
    try:
        # Find profiles matching timers
        order_timers = [timer_for_level(l) for l in ADAPTIVE_PRESSURE_ORDER]
        idx = order_timers.index(stable_until) if stable_until in order_timers else -1
        if idx >= 0 and idx + 1 < len(order_timers):
            window = f"{stable_until/1000:.1f}–{order_timers[idx+1]/1000:.1f}s"
        else:
            window = f"~{stable_until/1000:.1f}s"
    except Exception:
        window = f"~{stable_until/1000:.1f}s"
    return {
        "threshold_ms": stable_until,
        "comfort_window": window,
        "stable_until_ms": stable_until,
    }
