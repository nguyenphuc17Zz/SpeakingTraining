"""Situational scoring — server-owned."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Dim:
    score: float
    confidence: float = 0.85
    evidence: list[str] = field(default_factory=list)


@dataclass
class SituationalAssessment:
    task_completion: Dim
    intent_accuracy: Dim
    context_fit: Dim
    naturalness: Dim
    grammar: Dim
    register: Dim
    reaction: Dim
    recovery: Dim
    overall: Dim
    timed_out: bool = False
    late_response: bool = False

    def to_dict(self) -> dict[str, Any]:
        def d(x: Dim): return {"score": x.score, "confidence": x.confidence, "evidence": x.evidence}
        return {
            "task_completion": d(self.task_completion),
            "intent_accuracy": d(self.intent_accuracy),
            "context_fit": d(self.context_fit),
            "naturalness": d(self.naturalness),
            "grammar": d(self.grammar),
            "register": d(self.register),
            "reaction": d(self.reaction),
            "recovery": d(self.recovery),
            "overall": d(self.overall),
            "timed_out": self.timed_out,
            "late_response": self.late_response,
        }


WEIGHTS = {
    "situational_roleplay": {"task_completion": 0.30, "intent_accuracy": 0.20, "context_fit": 0.15, "naturalness": 0.10, "grammar": 0.10, "register": 0.10, "reaction": 0.05},
    "situational_scenario": {"task_completion": 0.30, "intent_accuracy": 0.20, "context_fit": 0.15, "naturalness": 0.15, "grammar": 0.10, "reaction": 0.10},
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


def build_situational_assessment(sub_mode: str, *, reaction_latency_ms, timer_limit_ms, speech_confidence, task_completion=70, intent_accuracy=70, context_fit=70, naturalness=70, grammar=70, register_score=70, recovery=80, timed_out=False, late_response=False, independence="independent") -> SituationalAssessment:
    if timed_out:
        return SituationalAssessment(
            task_completion=Dim(10, 0.9, ["Timed out"]),
            intent_accuracy=Dim(0,0.9,[]),
            context_fit=Dim(0,0.9,[]),
            naturalness=Dim(0,0.9,[]),
            grammar=Dim(0,0.9,[]),
            register=Dim(0,0.9,[]),
            reaction=Dim(10,0.9,["Timed out"]),
            recovery=Dim(0,0.9,[]),
            overall=Dim(15,0.9,["Timed out"]),
            timed_out=True,
            late_response=False,
        )
    reaction_dim = _reaction_score(reaction_latency_ms, timer_limit_ms, speech_confidence)
    indep_mult = 1.0 if independence=="independent" else 0.7
    # Weight
    weights = WEIGHTS.get(sub_mode, WEIGHTS["situational_roleplay"])
    dim_map = {
        "task_completion": task_completion * indep_mult,
        "intent_accuracy": intent_accuracy,
        "context_fit": context_fit,
        "naturalness": naturalness,
        "grammar": grammar,
        "register": register_score,
        "reaction": reaction_dim.score,
        "recovery": recovery,
    }
    total = sum(weights.values())
    overall = sum(dim_map.get(k,70)*w for k,w in weights.items())/total if total else 70
    if late_response:
        overall = max(0, overall-12)
    if intent_accuracy < 50:
        overall = min(overall, 55)
    return SituationalAssessment(
        task_completion=Dim(float(task_completion),0.85,["Task"]),
        intent_accuracy=Dim(float(intent_accuracy),0.85,["Intent"]),
        context_fit=Dim(float(context_fit),0.80,["Context"]),
        naturalness=Dim(float(naturalness),0.80,["Naturalness"]),
        grammar=Dim(float(grammar),0.80,["Grammar"]),
        register=Dim(float(register_score),0.80,["Register"]),
        reaction=reaction_dim,
        recovery=Dim(float(recovery),0.75,["Recovery"]),
        overall=Dim(round(overall,1),0.82,["Weighted situational policy"]),
        timed_out=False,
        late_response=late_response,
    )
