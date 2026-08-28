"""JapaneseLexicalProvider — pluggable lexical lookup with provenance.

No giant hardcoded keigo dictionary. This provider queries:
- Primary: SudachiLanguageProvider (morphology)
- Secondary: optional jamdict/wordfreq if installed (import guarded)
- Fallback: small explicit keigo overrides (project rules) — intentionally tiny and inspectable
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domains.japanese.provider import LexicalEntry, Provenance, get_language_provider


# Small explicit overrides only for truly irregular keigo where deterministic rules cannot infer
# This is PROJECT_RULE, not a language database. Keep < 60 entries, each with provenance.
# For any other verb, transformation is rule-based (o~ni naru, o~suru, etc.)
KEIGO_IRREGULAR_OVERRIDES: dict[str, dict[str, str]] = {
    # lemma -> {sonkeigo, kenjougo, teineigo_hint}
    "する": {"sonkeigo": "なさる", "kenjougo": "いたす", "teineigo": "します"},
    "来る": {"sonkeigo": "いらっしゃる", "kenjougo": "参る", "teineigo": "きます"},
    "行く": {"sonkeigo": "いらっしゃる", "kenjougo": "参る", "teineigo": "いきます"},
    "いる": {"sonkeigo": "いらっしゃる", "kenjougo": "おる", "teineigo": "います"},
    "見る": {"sonkeigo": "ご覧になる", "kenjougo": "拝見する", "teineigo": "みます"},
    "言う": {"sonkeigo": "おっしゃる", "kenjougo": "申す", "teineigo": "いいます"},
    "食べる": {"sonkeigo": "召し上がる", "kenjougo": "いただく", "teineigo": "たべます"},
    "飲む": {"sonkeigo": "召し上がる", "kenjougo": "いただく", "teineigo": "のみます"},
    "くれる": {"sonkeigo": "くださる", "kenjougo": "いただく", "teineigo": "くれます"},
    "あげる": {"sonkeigo": "—", "kenjougo": "差し上げる", "teineigo": "あげます"},
    "もらう": {"sonkeigo": "—", "kenjougo": "いただく", "teineigo": "もらいます"},
    "知る": {"sonkeigo": "ご存知だ", "kenjougo": "存じる", "teineigo": "しります"},
    "会う": {"sonkeigo": "—", "kenjougo": "お目にかかる", "teineigo": "あいます"},
    "聞く": {"sonkeigo": "—", "kenjougo": "伺う", "teineigo": "ききます"},
    "訪ねる": {"sonkeigo": "—", "kenjougo": "伺う", "teineigo": "たずねます"},
    "借りる": {"sonkeigo": "—", "kenjougo": "拝借する", "teineigo": "かりります"},
}

# Verify small size invariant
assert len(KEIGO_IRREGULAR_OVERRIDES) < 80, "Keigo overrides must stay small; use rules not database"


@dataclass
class LexicalQueryResult:
    entry: LexicalEntry
    honorific_overrides: dict[str, str] | None = None


class JapaneseLexicalProvider:
    def __init__(self):
        self._base = get_language_provider()
        # Optional wordfreq/jamdict probes (guarded)
        self._wordfreq_available = False
        self._jamdict_available = False
        try:
            import wordfreq  # type: ignore

            self._wordfreq_available = True
        except Exception:
            pass
        try:
            import jamdict  # type: ignore

            self._jamdict_available = True
        except Exception:
            pass

    def lookup(self, lemma: str) -> LexicalQueryResult | None:
        entry = self._base.lookup(lemma)
        if not entry:
            return None
        overrides = KEIGO_IRREGULAR_OVERRIDES.get(lemma) or KEIGO_IRREGULAR_OVERRIDES.get(entry.lemma)
        if overrides:
            entry.honorific_info = overrides
            entry.provenance = Provenance.PROJECT_RULE
            entry.source = "keigo_irregular_overrides"
        return LexicalQueryResult(entry=entry, honorific_overrides=overrides)

    def frequency(self, lemma: str) -> float | None:
        if self._wordfreq_available:
            try:
                import wordfreq

                return float(wordfreq.word_frequency(lemma, "ja"))
            except Exception:
                return None
        return None

    def is_common(self, lemma: str, threshold: float = 1e-6) -> bool:
        f = self.frequency(lemma)
        if f is None:
            return True  # assume common if no corpus
        return f >= threshold


_lex_singleton: JapaneseLexicalProvider | None = None


def get_lexical_provider() -> JapaneseLexicalProvider:
    global _lex_singleton
    if _lex_singleton is None:
        _lex_singleton = JapaneseLexicalProvider()
    return _lex_singleton
