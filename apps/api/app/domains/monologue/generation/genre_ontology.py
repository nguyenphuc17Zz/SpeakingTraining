"""Genre ontology — conceptual only, not a prompt database."""

from __future__ import annotations

from app.domains.monologue.contracts import SpeechDurationSec, SpeechGenre

# Genre → preferred structure (used by DiscourseStructureAnalyzer and support generation)
GENRE_STRUCTURE: dict[SpeechGenre, list[str]] = {
    SpeechGenre.PERSONAL: ["opening", "background", "episode", "reflection", "conclusion"],
    SpeechGenre.STORY: ["opening", "setting", "development", "climax", "conclusion"],
    SpeechGenre.OPINION: ["position", "reason", "example", "counterpoint", "conclusion"],
    SpeechGenre.EXPLANATION: ["opening", "definition", "steps", "example", "summary"],
    SpeechGenre.COMPARISON: ["opening", "option_a", "option_b", "comparison", "conclusion"],
    SpeechGenre.ARGUMENT: ["position", "reason", "evidence", "counterargument", "conclusion"],
    SpeechGenre.PROBLEM_SOLUTION: ["problem", "cause", "impact", "solution", "next_step"],
    SpeechGenre.REFLECTION: ["opening", "experience", "analysis", "learning", "conclusion"],
    SpeechGenre.SUMMARY: ["opening", "main_points", "key_details", "summary"],
    SpeechGenre.REPORT: ["status", "problem", "impact", "action", "next_step"],
    SpeechGenre.INTERVIEW: ["position", "reason", "evidence", "conclusion"],
    SpeechGenre.BUSINESS_UPDATE: ["status", "progress", "issue", "plan", "request"],
    SpeechGenre.PRESENTATION: ["opening", "point", "reason", "example", "conclusion"],
    SpeechGenre.PERSUASION: ["hook", "position", "reason", "evidence", "call_to_action"],
    SpeechGenre.CRITIQUE: ["opening", "strengths", "weaknesses", "suggestion", "conclusion"],
    SpeechGenre.PREDICTION: ["opening", "trend", "reason", "impact", "conclusion"],
}

# Genre → natural duration affinity (sec)
GENRE_DURATION_AFFINITY: dict[SpeechGenre, list[int]] = {
    SpeechGenre.PERSONAL: [30, 60, 90],
    SpeechGenre.STORY: [60, 90, 120],
    SpeechGenre.OPINION: [60, 90, 120],
    SpeechGenre.EXPLANATION: [60, 90, 120],
    SpeechGenre.COMPARISON: [60, 90, 120],
    SpeechGenre.ARGUMENT: [90, 120, 180],
    SpeechGenre.PROBLEM_SOLUTION: [90, 120, 180],
    SpeechGenre.REFLECTION: [60, 90, 120],
    SpeechGenre.SUMMARY: [60, 90],
    SpeechGenre.REPORT: [60, 90, 120],
    SpeechGenre.INTERVIEW: [60, 90, 120],
    SpeechGenre.BUSINESS_UPDATE: [60, 90, 120],
    SpeechGenre.PRESENTATION: [90, 120, 300],
    SpeechGenre.PERSUASION: [90, 120, 180],
    SpeechGenre.CRITIQUE: [90, 120, 180],
    SpeechGenre.PREDICTION: [60, 90, 120],
}

# Genre → register hint
GENRE_REGISTER: dict[SpeechGenre, str] = {
    SpeechGenre.PERSONAL: "casual_or_polite",
    SpeechGenre.STORY: "polite",
    SpeechGenre.OPINION: "polite",
    SpeechGenre.EXPLANATION: "polite",
    SpeechGenre.COMPARISON: "polite",
    SpeechGenre.ARGUMENT: "polite",
    SpeechGenre.PROBLEM_SOLUTION: "polite",
    SpeechGenre.REFLECTION: "polite",
    SpeechGenre.SUMMARY: "polite",
    SpeechGenre.REPORT: "business",
    SpeechGenre.INTERVIEW: "business",
    SpeechGenre.BUSINESS_UPDATE: "business",
    SpeechGenre.PRESENTATION: "presentation",
    SpeechGenre.PERSUASION: "polite",
    SpeechGenre.CRITIQUE: "polite",
    SpeechGenre.PREDICTION: "polite",
}

ALL_GENRES: list[SpeechGenre] = list(SpeechGenre)

# Conceptual topic domains — broad, not a topic list
from app.domains.monologue.contracts import SpeechTopicDomain
ALL_DOMAINS: list[SpeechTopicDomain] = list(SpeechTopicDomain)
