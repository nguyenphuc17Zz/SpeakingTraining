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

    @staticmethod
    def coherence_score(
        idea_density: dict | None,
        discourse: dict,
        filler_ratio: float | None = None,
        pause_breakdown: int | None = None,
    ) -> dict:
        # Deterministic support for AI coherence (§27)
        # Each dimension 0-100
        missing = discourse.get("missing_elements", [])
        has_conclusion = "conclusion" not in missing
        connector_q = discourse.get("connector_quality", "missing")

        idea_prog = 80
        if missing and len(missing) >= 2:
            idea_prog = 55
        elif missing and len(missing) == 1:
            idea_prog = 70

        linkage = 60 if connector_q == "missing" else 85 if connector_q == "appropriate" else 70
        if connector_q == "repeated":
            linkage = 65

        # reference clarity: if no repeated subject drops detected, assume 75; else penalize
        reference = 75 if not idea_density or idea_density.get("repeated_ideas", 0) <= 1 else 60
        continuity = 80
        if idea_density and idea_density.get("repeated_ideas", 0) > 2:
            continuity = 60

        conclusion_q = 90 if has_conclusion else 45

        # Adjust for breakdowns/filler spam
        if pause_breakdown and pause_breakdown >= 2:
            idea_prog = max(30, idea_prog - 15)
        if filler_ratio and filler_ratio > 0.15:
            linkage = max(30, linkage - 10)

        overall = round((idea_prog + linkage + reference + continuity + conclusion_q) / 5, 1)
        return {
            "idea_progression": idea_prog,
            "logical_linkage": linkage,
            "reference_clarity": reference,
            "topic_continuity": continuity,
            "conclusion_quality": conclusion_q,
            "overall": overall,
        }
