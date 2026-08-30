"""Pressure profiles for Reflex Speaking — configurable timer limits and difficulty mapping."""

from enum import Enum


class PressureLevel(str, Enum):
    INFINITE = "infinite"
    RELAXED = "relaxed"
    NORMAL = "normal"
    FAST = "fast"
    REFLEX = "reflex"
    EXTREME = "extreme"


PRESSURE_PROFILES: dict[str, dict] = {
    PressureLevel.INFINITE.value: {
        "label": "Infinite",
        "label_ja": "無制限",
        "timer_limit_ms": 0,
        "description": "Không giới hạn thời gian, tự do luyện tập (∞).",
        "difficulty": "all",
    },
    PressureLevel.RELAXED.value: {
        "label": "Relaxed",
        "label_ja": "ゆっくり",
        "timer_limit_ms": 6000,
        "description": "Thong thả, tập trung độ chính xác (6.0s).",
        "difficulty": "all",
    },
    PressureLevel.NORMAL.value: {
        "label": "Normal",
        "label_ja": "普通",
        "timer_limit_ms": 4000,
        "description": "Nhịp tự nhiên, cân bằng tốc độ & chính xác (4.0s).",
        "difficulty": "all",
    },
    PressureLevel.FAST.value: {
        "label": "Fast",
        "label_ja": "速め",
        "timer_limit_ms": 3000,
        "description": "Tăng áp lực, luyện phản xạ nhanh (3.0s).",
        "difficulty": "all",
    },
    PressureLevel.REFLEX.value: {
        "label": "Reflex",
        "label_ja": "瞬発",
        "timer_limit_ms": 2500,
        "description": "Phản xạ tức thì, như hội thoại thực (2.5s).",
        "difficulty": "all",
    },
    PressureLevel.EXTREME.value: {
        "label": "Extreme",
        "label_ja": "超速",
        "timer_limit_ms": 1800,
        "description": "Thử thách giới hạn, phản xạ chớp mắt (1.8s).",
        "difficulty": "all",
    },
}

# Adaptive presets for Learning Engine recommendation
ADAPTIVE_PRESSURE_ORDER = [
    PressureLevel.INFINITE.value,
    PressureLevel.RELAXED.value,
    PressureLevel.NORMAL.value,
    PressureLevel.FAST.value,
    PressureLevel.REFLEX.value,
    PressureLevel.EXTREME.value,
]


def get_pressure_profile(level: str) -> dict:
    """Returns pressure profile dict; falls back to NORMAL."""
    return PRESSURE_PROFILES.get(level, PRESSURE_PROFILES[PressureLevel.NORMAL.value])


def next_pressure_level(current: str, harder: bool = True) -> str:
    """Moves 1 tier up/down, bounded."""
    try:
        idx = ADAPTIVE_PRESSURE_ORDER.index(current)
    except ValueError:
        idx = 2  # normal
    if harder:
        return ADAPTIVE_PRESSURE_ORDER[min(len(ADAPTIVE_PRESSURE_ORDER) - 1, idx + 1)]
    return ADAPTIVE_PRESSURE_ORDER[max(0, idx - 1)]


def timer_for_level(level: str) -> int:
    return get_pressure_profile(level)["timer_limit_ms"]
