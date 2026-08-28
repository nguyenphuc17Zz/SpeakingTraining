"""Keigo scoring — server-owned weights."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Dim:
    score: float
    confidence: float = 0.85
    evidence: list[str] = field(default_factory=list)


@dataclass
class KeigoAssessment:
    role_accuracy: Dim
    register_accuracy: Dim
    keigo_accuracy: Dim
    grammar: Dim
    naturalness: Dim
    context_fit: Dim
    reaction: Dim
    independence: Dim
    completeness: Dim
    overall: Dim
    double_keigo: dict[str, Any] | None = None
    provenance: dict[str, Any] | None = None
    timed_out: bool = False
    late_response: bool = False

    def to_dict(self) -> dict[str, Any]:
        def d(x: Dim): return {"score": x.score, "confidence": x.confidence, "evidence": x.evidence}
        return {
            "role_accuracy": d(self.role_accuracy),
            "register_accuracy": d(self.register_accuracy),
            "keigo_accuracy": d(self.keigo_accuracy),
            "grammar": d(self.grammar),
            "naturalness": d(self.naturalness),
            "context_fit": d(self.context_fit),
            "reaction": d(self.reaction),
            "independence": d(self.independence),
            "completeness": d(self.completeness),
            "overall": d(self.overall),
            "double_keigo": self.double_keigo,
            "provenance": self.provenance,
            "timed_out": self.timed_out,
            "late_response": self.late_response,
        }


WEIGHTS = {
    "keigo_sonkeigo": {"role_accuracy": 0.20, "register_accuracy": 0.20, "keigo_accuracy": 0.20, "grammar": 0.15, "naturalness": 0.10, "context_fit": 0.10, "reaction": 0.05},
    "keigo_kenjougo": {"role_accuracy": 0.20, "register_accuracy": 0.20, "keigo_accuracy": 0.20, "grammar": 0.15, "naturalness": 0.10, "context_fit": 0.10, "reaction": 0.05},
    "keigo_teineigo": {"register_accuracy": 0.25, "keigo_accuracy": 0.20, "grammar": 0.20, "naturalness": 0.15, "context_fit": 0.10, "reaction": 0.10},
    "keigo_transformation": {"register_accuracy": 0.25, "keigo_accuracy": 0.25, "grammar": 0.20, "naturalness": 0.15, "context_fit": 0.10, "reaction": 0.05},
    "keigo_context": {"context_fit": 0.25, "keigo_accuracy": 0.20, "role_accuracy": 0.20, "naturalness": 0.15, "register_accuracy": 0.10, "reaction": 0.10},
    "keigo_doctor": {"keigo_accuracy": 0.30, "grammar": 0.20, "naturalness": 0.20, "context_fit": 0.15, "role_accuracy": 0.10, "reaction": 0.05},
    "keigo_naturalness": {"naturalness": 0.30, "context_fit": 0.20, "register_accuracy": 0.20, "grammar": 0.15, "keigo_accuracy": 0.10, "reaction": 0.05},
}


def _reaction_score(latency, timer, conf):
    if latency is None or (conf is not None and conf < 0.4):
        return Dim(50, 0.3, ["Latency unreliable"])
    if not timer:
        return Dim(75, 0.6, [f"Latency {latency:.0f}ms"])
    r = latency / timer
    if r < 0.4: s = 95
    elif r < 0.6: s = 85
    elif r < 0.8: s = 72
    elif r < 1.0: s = 58
    else: s = 32
    return Dim(float(s), 0.85, [f"Reaction {latency:.0f}ms / {timer}ms"])


def build_keigo_assessment(sub_mode: str, *, reaction_latency_ms, timer_limit_ms, speech_confidence, role_accuracy=80, register_accuracy=80, keigo_accuracy=80, grammar=80, naturalness=80, context_fit=80, completeness=80, independence="independent", timed_out=False, late_response=False, double_keigo=None) -> KeigoAssessment:
    if timed_out:
        role = Dim(10, 0.9, ["Timed out"])
        overall = Dim(15, 0.9, ["Timed out"])
        return KeigoAssessment(role, Dim(10,0.9,[]), Dim(0,0.9,[]), Dim(0,0.9,[]), Dim(0,0.9,[]), Dim(0,0.9,[]), Dim(10,0.9,["Timed out"]), Dim(50,0.5,[]), Dim(20,0.9,[]), overall, double_keigo, None, True, False, reaction_latency_ms, None, timer_limit_ms)

    def mk(v, ev=""): return Dim(float(v), 0.85, [ev])
    reaction_dim = _reaction_score(reaction_latency_ms, timer_limit_ms, speech_confidence)
    indep_score = 100 if independence=="independent" else 70 if independence=="assisted_hint" else 50
    independence_dim = Dim(float(indep_score), 0.85, [independence])

    # Weight
    weights = WEIGHTS.get(sub_mode, WEIGHTS["keigo_transformation"])
    dim_map = {
        "role_accuracy": role_accuracy,
        "register_accuracy": register_accuracy,
        "keigo_accuracy": keigo_accuracy,
        "grammar": grammar,
        "naturalness": naturalness,
        "context_fit": context_fit,
        "reaction": reaction_dim.score,
        "completeness": completeness,
    }
    total = sum(weights.values())
    overall_score = sum(dim_map.get(k,70)*w for k,w in weights.items())/total if total else 70
    if late_response:
        overall_score = max(0, overall_score-12)
    if keigo_accuracy < 50 and reaction_dim.score>80:
        overall_score = min(overall_score, 55)
    if naturalness < 50:
        overall_score = min(overall_score, 65)

    return KeigoAssessment(
        role_accuracy=mk(role_accuracy),
        register_accuracy=mk(register_accuracy),
        keigo_accuracy=mk(keigo_accuracy),
        grammar=mk(grammar),
        naturalness=mk(naturalness),
        context_fit=mk(context_fit),
        reaction=reaction_dim,
        independence=independence_dim,
        completeness=mk(completeness),
        overall=Dim(round(overall_score,1), 0.80, ["Weighted keigo policy"]),
        double_keigo=double_keigo,
        provenance=None,
        timed_out=timed_out,
        late_response=late_response,
    )
