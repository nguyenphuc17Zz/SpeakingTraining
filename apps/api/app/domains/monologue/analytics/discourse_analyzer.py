"""DiscourseStructureAnalyzer §25/26 + Coherence scoring §27."""

from __future__ import annotations

import re
from typing import Any

from app.domains.monologue.contracts import ConnectorClass, SpeechGenre
from app.domains.monologue.generation.genre_ontology import GENRE_STRUCTURE

# Connector lexical cues → class (small resource, not full inventory)
CONNECTOR_LEXICON: dict[str, ConnectorClass] = {
    "まず": ConnectorClass.SEQUENCE,
    "次に": ConnectorClass.SEQUENCE,
    "そして": ConnectorClass.ADDITION,
    "また": ConnectorClass.ADDITION,
    "さらに": ConnectorClass.ADDITION,
    "一方で": ConnectorClass.CONTRAST,
    "しかし": ConnectorClass.CONTRAST,
    "でも": ConnectorClass.CONTRAST,
    "そのため": ConnectorClass.CAUSE,
    "だから": ConnectorClass.CAUSE,
    "なので": ConnectorClass.CAUSE,
    "したがって": ConnectorClass.EFFECT,
    "結果": ConnectorClass.EFFECT,
    "例えば": ConnectorClass.EXAMPLE,
    "たとえば": ConnectorClass.EXAMPLE,
    "具体的": ConnectorClass.EXAMPLE,
    "つまり": ConnectorClass.CLARIFICATION,
    "要するに": ConnectorClass.CLARIFICATION,
    "特に": ConnectorClass.EMPHASIS,
    "もちろん": ConnectorClass.EMPHASIS,
    "まとめると": ConnectorClass.SUMMARY,
    "結論として": ConnectorClass.CONCLUSION,
    "最後に": ConnectorClass.CONCLUSION,
    "以上": ConnectorClass.CONCLUSION,
}


class DiscourseStructureAnalyzer:
    @staticmethod
    def expected_for_genre(genre: SpeechGenre | str) -> list[str]:
        if isinstance(genre, str):
            try:
                genre = SpeechGenre(genre.lower())
            except Exception:
                return ["opening", "point", "reason", "example", "conclusion"]
        return GENRE_STRUCTURE.get(genre, ["opening", "point", "reason", "example", "conclusion"])

    def analyze(
        self,
        transcript: str,
        genre: SpeechGenre | str,
    ) -> dict[str, Any]:
        expected = self.expected_for_genre(genre)
        # Heuristic detection: look for cue markers for each element
        detected: list[str] = []
        # Simple: sentences containing certain markers → map to structure
        sentences = [s.strip() for s in re.split(r"[。！？\n]+", transcript) if s.strip()]
        text = transcript

        # Opening: first sentence
        if sentences:
            detected.append("opening")

        # Detect markers
        if re.search(r"(私の意見|思います|考えます)", text):
            detected.append("position" if "position" in expected else "opinion")
        if re.search(r"(理由|なぜなら|なぜ|ため)", text):
            detected.append("reason" if "reason" in expected else "cause")
        if any(c in text for c in ["例えば", "たとえば", "具体例", "例として"]):
            detected.append("example")
        if re.search(r"(一方|しかし|でも|反対)", text):
            detected.append("contrast" if "contrast" in expected else "counterpoint")
        if re.search(r"(結論|まとめ|以上|最後に)", text):
            detected.append("conclusion")
        # For report/business
        if "status" in expected and re.search(r"(現状|状況|今)", text):
            detected.append("status")
        if "problem" in expected and re.search(r"(問題|課題|困)", text):
            detected.append("problem")

        # Deduplicate preserve order
        uniq_detected: list[str] = []
        for d in detected:
            if d not in uniq_detected:
                uniq_detected.append(d)

        missing = [e for e in expected if e not in uniq_detected]

        # Connector analysis
        connector_counts: dict[str, int] = {}
        connector_quality = "missing"
        total_connectors = 0
        for cue, cls in CONNECTOR_LEXICON.items():
            cnt = text.count(cue)
            if cnt:
                connector_counts[cls.value] = connector_counts.get(cls.value, 0) + cnt
                total_connectors += cnt

        if total_connectors == 0:
            connector_quality = "missing"
        elif total_connectors >= 3 and len(connector_counts) >= 3:
            connector_quality = "appropriate"
        elif total_connectors >= 5 and len(connector_counts) <= 2:
            connector_quality = "repeated"
        elif total_connectors >= 1:
            connector_quality = "present"

        # Check misused: heuristic — no check without semantic AI, mark present
        return {
            "detected_structure": uniq_detected,
            "expected_structure": expected,
            "missing_elements": missing,
            "connector_counts": connector_counts,
            "connector_quality": connector_quality,
            "total_connectors": total_connectors,
        }

    @classmethod
    def compute_centering_cohesion(cls, transcript: str) -> dict[str, Any]:
        """
        SOTA Centering Theory (Grosz, Joshi, & Weinstein 1995) Transition Engine.
        Analyzes discourse entity salience and backward/forward looking centers (Cb, Cp)
        via Japanese grammatical particle indicators (は, が, も, を).
        Computes Rhetorical Cohesion Flow Index based on Markovian transition states.
        """
        sentences = [s.strip() for s in re.split(r"[。！？\n]+", transcript) if s.strip()]
        if len(sentences) <= 1:
            return {
                "cohesion_flow_score": 85.0,
                "transitions": ["ESTABLISH"],
                "transition_distribution": {"CONTINUE": 0, "RETAIN": 0, "SMOOTH_SHIFT": 0, "ROUGH_SHIFT": 0},
                "dominant_transition": "ESTABLISH",
            }

        # Extract centers per sentence: (Cb: backward topic, Cp: forward preferred focus)
        centers_seq: list[tuple[str | None, str | None]] = []
        for s in sentences:
            topic = None
            focus = None
            m_wa = re.search(r"([一-龯ぁ-んァ-ンa-zA-Z0-9]+)は", s)
            if m_wa:
                topic = m_wa.group(1)
            m_ga = re.search(r"([一-龯ぁ-んァ-ンa-zA-Z0-9]+)(が|も|を)", s)
            if m_ga:
                focus = m_ga.group(1)
            if not focus:
                focus = topic
            if not topic:
                topic = focus
            centers_seq.append((topic, focus))

        # Evaluate transitions
        transitions: list[str] = []
        weights: list[float] = []

        TRANSITION_WEIGHTS = {
            "CONTINUE": 1.0,        # Same topic, highest cohesion
            "RETAIN": 0.85,         # Same topic, preparing focus shift
            "SMOOTH_SHIFT": 0.70,   # Topic shifts to previous focus
            "ROUGH_SHIFT": 0.35,    # Abrupt topic jump / discontinuity
            "NEUTRAL": 0.75,        # Implicit pronoun / ellipsed center
        }

        for i in range(1, len(centers_seq)):
            prev_cb, prev_cp = centers_seq[i - 1]
            curr_cb, curr_cp = centers_seq[i]

            if not prev_cb or not curr_cb:
                tr = "NEUTRAL"
            elif curr_cb == prev_cb:
                if curr_cb == curr_cp:
                    tr = "CONTINUE"
                else:
                    tr = "RETAIN"
            elif prev_cp and curr_cb == prev_cp:
                tr = "SMOOTH_SHIFT"
            else:
                tr = "ROUGH_SHIFT"

            transitions.append(tr)
            weights.append(TRANSITION_WEIGHTS.get(tr, 0.75))

        dist = {
            "CONTINUE": transitions.count("CONTINUE"),
            "RETAIN": transitions.count("RETAIN"),
            "SMOOTH_SHIFT": transitions.count("SMOOTH_SHIFT"),
            "ROUGH_SHIFT": transitions.count("ROUGH_SHIFT"),
        }

        avg_weight = sum(weights) / max(1, len(weights))
        cohesion_score = round(100.0 * avg_weight, 1)

        dominant = max(dist.keys(), key=lambda k: dist[k]) if any(dist.values()) else "CONTINUE"

        return {
            "cohesion_flow_score": cohesion_score,
            "transitions": transitions,
            "transition_distribution": dist,
            "dominant_transition": dominant,
        }

    @classmethod
    def coherence_score(
        cls,
        idea_density: dict | None,
        discourse: dict,
        filler_ratio: float | None = None,
        pause_breakdown: int | None = None,
        transcript: str = "",
    ) -> dict:
        """
        Calculates multidimensional discourse coherence score augmented with Centering Cohesion Flow.
        """
        missing = discourse.get("missing_elements", [])
        has_conclusion = "conclusion" not in missing
        connector_q = discourse.get("connector_quality", "missing")

        # Centering analysis if transcript available
        centering = cls.compute_centering_cohesion(transcript) if transcript else None
        centering_score = centering["cohesion_flow_score"] if centering else 80.0

        idea_prog = 80
        if missing and len(missing) >= 2:
            idea_prog = 55
        elif missing and len(missing) == 1:
            idea_prog = 70

        linkage = 60 if connector_q == "missing" else 85 if connector_q == "appropriate" else 70
        if connector_q == "repeated":
            linkage = 65

        # Incorporate Centering Transition into logical linkage & topic continuity
        if centering:
            linkage = round(0.50 * linkage + 0.50 * centering_score, 1)

        # reference clarity: if no repeated subject drops detected, assume 75; else penalize
        reference = 75 if not idea_density or idea_density.get("repeated_ideas", 0) <= 1 else 60

        # Topic continuity driven by Centering Theory
        continuity = round(centering_score, 1) if centering else 80.0
        if idea_density and idea_density.get("repeated_ideas", 0) > 2:
            continuity = max(40.0, continuity - 15.0)

        conclusion_q = 90 if has_conclusion else 45

        # Adjust for breakdowns/filler spam
        if pause_breakdown and pause_breakdown >= 2:
            idea_prog = max(30, idea_prog - 15)
        if filler_ratio and filler_ratio > 0.15:
            linkage = max(30.0, linkage - 10.0)

        overall = round((idea_prog + linkage + reference + continuity + conclusion_q) / 5.0, 1)
        return {
            "idea_progression": idea_prog,
            "logical_linkage": linkage,
            "reference_clarity": reference,
            "topic_continuity": continuity,
            "conclusion_quality": conclusion_q,
            "overall": overall,
            "centering_cohesion": centering,
        }
