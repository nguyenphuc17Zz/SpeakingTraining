"""Reflex scoring policy — deterministic, server-owned.

Implements ReflexAssessment with 7 dimensions per spec #29-31.
No hard-coded UI percentages; policy lives here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ReflexSubMode(str, Enum):
    CONJUGATION = "reflex_conjugation"
    QNA = "reflex_qna"
    TRANSFORMATION = "reflex_transformation"
    CONTEXT = "reflex_context"


@dataclass
class DimensionScore:
    score: float  # 0-100
    confidence: float = 0.85  # 0-1
    evidence: list[str] = field(default_factory=list)


@dataclass
class ReflexAssessment:
    reaction: DimensionScore
    accuracy: DimensionScore
    naturalness: DimensionScore
    fluency: DimensionScore
    context_fit: DimensionScore
    independence: DimensionScore
    completeness: DimensionScore
    overall: DimensionScore
    timed_out: bool = False
    late_response: bool = False
    # Raw latencies for analytics
    reaction_latency_ms: float | None = None
    semantic_latency_ms: float | None = None
    timer_limit_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        def dim(d: DimensionScore) -> dict:
            return {"score": d.score, "confidence": d.confidence, "evidence": d.evidence}
        return {
            "reaction": dim(self.reaction),
            "accuracy": dim(self.accuracy),
            "naturalness": dim(self.naturalness),
            "fluency": dim(self.fluency),
            "context_fit": dim(self.context_fit),
            "independence": dim(self.independence),
            "completeness": dim(self.completeness),
            "overall": dim(self.overall),
            "timed_out": self.timed_out,
            "late_response": self.late_response,
            "reaction_latency_ms": self.reaction_latency_ms,
            "semantic_latency_ms": self.semantic_latency_ms,
            "timer_limit_ms": self.timer_limit_ms,
        }


# Weight policies per sub-mode (must sum ~1.0 for overall)
WEIGHTS: dict[str, dict[str, float]] = {
    ReflexSubMode.CONJUGATION.value: {
        "accuracy": 0.50,
        "reaction": 0.30,
        "fluency": 0.20,
    },
    ReflexSubMode.QNA.value: {
        "context_fit": 0.30,
        "accuracy": 0.25,  # grammar correctness
        "reaction": 0.20,
        "naturalness": 0.15,
        "fluency": 0.10,
    },
    ReflexSubMode.CONTEXT.value: {
        "context_fit": 0.30,
        "naturalness": 0.25,
        "accuracy": 0.20,
        "reaction": 0.15,
        "fluency": 0.10,
    },
    ReflexSubMode.TRANSFORMATION.value: {
        "accuracy": 0.40,  # transformation correctness
        "context_fit": 0.30,  # semantic preservation
        "reaction": 0.15,
        "naturalness": 0.15,
    },
}


def _reaction_score(latency_ms: float | None, timer_limit_ms: int | None, confidence: float | None) -> DimensionScore:
    """Maps reaction latency to score. Fast but not sole proficiency indicator."""
    if latency_ms is None or confidence is not None and confidence < 0.4:
        return DimensionScore(score=50.0, confidence=0.3, evidence=["Reaction latency unreliable (low VAD confidence)"])
    if timer_limit_ms is None or timer_limit_ms <= 0:
        # No timer => neutral
        return DimensionScore(score=75.0, confidence=0.6, evidence=[f"Latency {latency_ms:.0f}ms (no timer)"])
    ratio = latency_ms / timer_limit_ms
    # Scoring: <0.4 ratio => 95+, <0.6 => 85, <0.8 => 70, <1.0 => 55, >1.0 => 30
    if ratio < 0.4:
        s = 95.0
    elif ratio < 0.6:
        s = 85.0
    elif ratio < 0.8:
        s = 72.0
    elif ratio < 1.0:
        s = 58.0
    else:
        s = 32.0
    # Bonus for very fast independent correct will be applied via accuracy multiplier elsewhere
    return DimensionScore(score=s, confidence=0.85, evidence=[f"Reaction {latency_ms:.0f}ms / {timer_limit_ms}ms (ratio {ratio:.2f})"])


def _independence_score(level: str | None) -> DimensionScore:
    mapping = {
        "independent": (100.0, 0.95, "Independent"),
        "assisted_hint": (70.0, 0.85, "With hint"),
        "retry_success": (55.0, 0.80, "Retry success"),
        "scaffolded": (40.0, 0.85, "Scaffolded"),
        None: (100.0, 0.5, "Unknown"),
    }
    sc, conf, ev = mapping.get(level or "independent", (70.0, 0.6, "Assisted"))
    return DimensionScore(score=sc, confidence=conf, evidence=[ev])


class ReflexScoringPolicy:
    """Server-owned scoring policy."""

    @classmethod
    def build(
        cls,
        sub_mode: str,
        *,
        reaction_latency_ms: float | None,
        timer_limit_ms: int | None,
        speech_confidence: float | None,
        accuracy_score: float,  # 0-100 from conjugation or grammar check
        naturalness_score: float | None = None,
        fluency_score: float | None = None,
        context_fit_score: float | None = None,
        completeness_score: float | None = None,
        independence_level: str = "independent",
        timed_out: bool = False,
        late_response: bool = False,
        semantic_latency_ms: float | None = None,
    ) -> ReflexAssessment:
        # Normalize None scores to 70 neutral
        nat = naturalness_score if naturalness_score is not None else accuracy_score
        flu = fluency_score if fluency_score is not None else 75.0
        ctx = context_fit_score if context_fit_score is not None else accuracy_score
        comp = completeness_score if completeness_score is not None else (100.0 if not timed_out else 20.0)

        reaction_dim = _reaction_score(reaction_latency_ms, timer_limit_ms, speech_confidence)
        if timed_out:
            reaction_dim = DimensionScore(score=10.0, confidence=0.9, evidence=["Timed out — no response within limit"])
            accuracy_dim = DimensionScore(score=0.0, confidence=0.9, evidence=["No response"])
            # Keep other dims low but not zero to avoid harsh penalty
        else:
            accuracy_dim = DimensionScore(score=float(accuracy_score), confidence=0.85, evidence=["Accuracy from evaluation"])
        naturalness_dim = DimensionScore(score=float(nat), confidence=0.75, evidence=["Naturalness"])
        fluency_dim = DimensionScore(score=float(flu), confidence=0.70, evidence=["Fluency"])
        context_dim = DimensionScore(score=float(ctx), confidence=0.75, evidence=["Context fit"])
        independence_dim = _independence_score(independence_level)
        completeness_dim = DimensionScore(score=float(comp), confidence=0.80, evidence=["Completeness"])

        # Timeout overrides overall
        if timed_out:
            overall_score = 15.0
            overall_conf = 0.9
        else:
            weights = WEIGHTS.get(sub_mode, WEIGHTS[ReflexSubMode.QNA.value])
            # Map dimension names to dims
            dim_map = {
                "accuracy": accuracy_dim.score,
                "reaction": reaction_dim.score,
                "naturalness": naturalness_dim.score,
                "fluency": fluency_dim.score,
                "context_fit": context_dim.score,
                "completeness": completeness_dim.score,
            }
            total_w = sum(weights.values())
            overall_score = sum(dim_map.get(k, 70.0) * w for k, w in weights.items()) / total_w if total_w > 0 else 70.0
            # Independence is not weighted in overall but gates Perfect (see evaluator)
            # Apply late response penalty
            if late_response:
                overall_score = max(0.0, overall_score - 12.0)
            # Reaction should not dominate correctness: if accuracy <50 and reaction >80, cap overall
            if accuracy_dim.score < 50 and reaction_dim.score > 80:
                overall_score = min(overall_score, 55.0)
            overall_conf = 0.80

        # Determine success threshold for Perfect etc: overall >=80 and accuracy >=75 and not timed_out/late
        return ReflexAssessment(
            reaction=reaction_dim,
            accuracy=accuracy_dim,
            naturalness=naturalness_dim,
            fluency=fluency_dim,
            context_fit=context_dim,
            independence=independence_dim,
            completeness=completeness_dim,
            overall=DimensionScore(score=round(overall_score, 1), confidence=overall_conf, evidence=["Weighted overall per sub-mode policy"]),
            timed_out=timed_out,
            late_response=late_response,
            reaction_latency_ms=reaction_latency_ms,
            semantic_latency_ms=semantic_latency_ms,
            timer_limit_ms=timer_limit_ms,
        )


def build_reflex_assessment(
    sub_mode: str,
    **kwargs,
) -> ReflexAssessment:
    return ReflexScoringPolicy.build(sub_mode, **kwargs)
