"""Pitch scoring — server-owned, not raw Hz."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Dim:
    score: float
    confidence: float = 0.85
    evidence: list[str] = field(default_factory=list)


@dataclass
class PitchAssessment:
    accent_pattern: Dim
    mora_alignment: Dim
    downstep: Dim
    contour: Dim
    stability: Dim
    overall: Dim
    confidence: float = 0.85
    timed_out: bool = False
    late_response: bool = False

    def to_dict(self) -> dict[str, Any]:
        def d(x: Dim): return {"score": x.score, "confidence": x.confidence, "evidence": x.evidence}
        return {
            "accent_pattern": d(self.accent_pattern),
            "mora_alignment": d(self.mora_alignment),
            "downstep": d(self.downstep),
            "contour": d(self.contour),
            "stability": d(self.stability),
            "overall": d(self.overall),
            "confidence": self.confidence,
            "timed_out": self.timed_out,
            "late_response": self.late_response,
        }


WEIGHTS = {
    "pitch_minimal_pair": {"lexical": 0.50, "accent_pattern": 0.30, "mora_accuracy": 0.15, "reaction": 0.05},
    "mora_length": {"lexical": 0.40, "mora_timing": 0.30, "length_accuracy": 0.20, "stability": 0.10},
    "vowel_devoicing": {"phonetic": 0.40, "duration": 0.25, "voicing": 0.20, "stability": 0.15},
    "pitch_contour": {"accent_pattern": 0.40, "mora_alignment": 0.25, "downstep": 0.15, "contour": 0.10, "stability": 0.10},
    "pitch_recognition": {"discrimination": 0.70, "lexical": 0.20, "reaction": 0.10},
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


def build_pitch_assessment(sub_mode: str, *, reaction_latency_ms, timer_limit_ms, speech_confidence, pitch_confidence, lexical_score=80, accent_pattern_score=80, mora_score=80, downstep_score=80, contour_score=80, stability_score=80, timed_out=False, late_response=False) -> PitchAssessment:
    if timed_out:
        return PitchAssessment(Dim(0,0.9,["Timed out"]), Dim(0,0.9,[]), Dim(0,0.9,[]), Dim(0,0.9,[]), Dim(0,0.9,[]), Dim(15,0.9,["Timed out"]), pitch_confidence or 0.9, True, False)

    reaction_dim = _reaction_score(reaction_latency_ms, timer_limit_ms, speech_confidence)
    # Handle low pitch confidence -> null score
    if pitch_confidence is not None and pitch_confidence < 0.35:
        # Unreliable F0
        return PitchAssessment(
            accent_pattern=Dim(0, 0.3, ["F0 unreliable"]),
            mora_alignment=Dim(mora_score, 0.5, ["Mora estimated"]),
            downstep=Dim(0, 0.3, ["Unreliable"]),
            contour=Dim(0, 0.3, ["Unreliable"]),
            stability=Dim(stability_score, 0.5, []),
            overall=Dim(0, 0.3, ["Retry audio"]),
            confidence=0.3,
            timed_out=False,
            late_response=late_response,
        )

    weights = WEIGHTS.get(sub_mode, WEIGHTS["pitch_contour"])
    # Map for pitch_contour
    if sub_mode == "pitch_contour":
        dim_map = {"accent_pattern": accent_pattern_score, "mora_alignment": mora_score, "downstep": downstep_score, "contour": contour_score, "stability": stability_score}
        total = sum(weights.values())
        overall = sum(dim_map.get(k,70)*w for k,w in weights.items())/total if total else 70
        if downstep_score < 50:
            overall = min(overall, 55)  # major penalty for wrong drop
        if accent_pattern_score < 50:
            overall = min(overall, 60)
    elif sub_mode == "mora_length":
        # lexical + mora
        overall = lexical_score*0.4 + mora_score*0.30 + downstep_score*0.20 + stability_score*0.10
    elif sub_mode == "pitch_minimal_pair":
        overall = lexical_score*0.50 + accent_pattern_score*0.30 + mora_score*0.15 + reaction_dim.score*0.05
    elif sub_mode == "vowel_devoicing":
        overall = lexical_score*0.40 + mora_score*0.25 + accent_pattern_score*0.20 + stability_score*0.15
    else:  # recognition
        overall = lexical_score*0.20 + accent_pattern_score*0.70 + reaction_dim.score*0.10

    if late_response:
        overall = max(0, overall-12)

    return PitchAssessment(
        accent_pattern=Dim(float(accent_pattern_score), 0.85, ["Accent pattern"]),
        mora_alignment=Dim(float(mora_score), 0.80, ["Mora alignment"]),
        downstep=Dim(float(downstep_score), 0.80, ["Downstep"]),
        contour=Dim(float(contour_score), 0.75, ["Contour"]),
        stability=Dim(float(stability_score), 0.75, ["Stability"]),
        overall=Dim(round(overall,1), 0.82, ["Weighted pitch policy"]),
        confidence=pitch_confidence or 0.85,
        timed_out=timed_out,
        late_response=late_response,
    )
