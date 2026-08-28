"""JapaneseLanguageResourceProvider — abstraction over Sudachi/pykakasi + pluggable lexical/corpus.

Implements Protocol to hide vendor. Deterministic first, AI never sole source.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from app.core.logging import logger


class Provenance(str, Enum):
    OFFICIAL_GUIDANCE = "official_guidance"
    LEXICAL_RESOURCE = "lexical_resource"
    MORPHOLOGICAL_ANALYZER = "morphological_analyzer"
    CORPUS = "corpus"
    PROJECT_RULE = "project_rule"
    AI_INFERENCE = "ai_inference"


@dataclass
class TokenAnalysis:
    surface: str
    lemma: str
    reading: str | None  # hiragana
    reading_kata: str | None
    pos: str  # 品詞大分類 e.g. 動詞, 名詞
    pos_detail: str | None
    inflection_type: str | None
    inflection_form: str | None
    features: dict[str, Any] = field(default_factory=dict)
    provenance: Provenance = Provenance.MORPHOLOGICAL_ANALYZER
    confidence: float = 0.95


@dataclass
class LexicalEntry:
    lemma: str
    reading: str | None
    pos: str
    verb_class: str | None  # ichidan/godan/suru/kuru
    semantic_category: str | None
    honorific_info: dict[str, Any] | None = None
    source: str = "lexical_provider"
    confidence: float = 0.90
    provenance: Provenance = Provenance.LEXICAL_RESOURCE


class JapaneseLanguageResourceProvider(Protocol):
    def analyze(self, text: str) -> list[TokenAnalysis]: ...
    def get_lemma(self, token: str) -> str | None: ...
    def get_reading(self, token: str) -> str | None: ...
    def get_pos(self, token: str) -> str | None: ...
    def normalize(self, text: str) -> str: ...
    def resolve_dictionary_form(self, token: str) -> str | None: ...
    def lookup(self, lemma: str) -> LexicalEntry | None: ...


class SudachiLanguageProvider:
    """Primary provider wrapping existing JapaneseReadingResolver + Sudachi.

    Reuses apps/api/app/domains/pronunciation/japanese/reading_resolver.py stack
    without duplicating init logic. Falls back to pykakasi when Sudachi unavailable.
    """

    def __init__(self):
        # Lazy import to reuse existing resolver without circular dependency
        try:
            from app.domains.pronunciation.japanese.reading_resolver import JapaneseReadingResolver

            self._resolver = JapaneseReadingResolver()
            self._sudachi_available = True
        except Exception as e:
            logger.warning(f"[JapaneseProvider] reading resolver unavailable: {e}")
            self._resolver = None
            self._sudachi_available = False
        # Direct sudachi for token analysis (separate from resolver's tokenizer)
        self._tokenizer = None
        try:
            from sudachipy import dictionary

            d = dictionary.Dictionary()
            self._tokenizer = d.create()
            from sudachipy.tokenizer import Tokenizer as SudTokenizer

            self._SplitMode = SudTokenizer.SplitMode.C
        except Exception:
            self._tokenizer = None
            self._SplitMode = None

    def analyze(self, text: str) -> list[TokenAnalysis]:
        if self._tokenizer and self._SplitMode is not None:
            try:
                morphemes = self._tokenizer.tokenize(text, self._SplitMode)
                out: list[TokenAnalysis] = []
                for m in morphemes:
                    surface = m.surface()
                    try:
                        # Sudachi morpheme API varies by version
                        dic_form = m.dictionary_form() if hasattr(m, "dictionary_form") else surface
                        reading = m.reading_form() if hasattr(m, "reading_form") else None
                        pos = m.part_of_speech()[0] if hasattr(m, "part_of_speech") else "UNKNOWN"
                        # inflection
                        infl_type = None
                        infl_form = None
                        if hasattr(m, "part_of_speech"):
                            # Sudachi doesn't expose inflection directly; leave None
                            pass
                    except Exception:
                        dic_form = surface
                        reading = None
                        pos = "UNKNOWN"
                    # Convert katakana reading to hiragana via resolver
                    hira = None
                    kata = reading
                    if reading and self._resolver:
                        try:
                            hira = self._resolver.to_hiragana(reading)
                        except Exception:
                            hira = None
                    out.append(
                        TokenAnalysis(
                            surface=surface,
                            lemma=dic_form,
                            reading=hira,
                            reading_kata=kata,
                            pos=pos,
                            pos_detail=None,
                            inflection_type=infl_type,
                            inflection_form=infl_form,
                            provenance=Provenance.MORPHOLOGICAL_ANALYZER,
                            confidence=0.96 if pos != "UNKNOWN" else 0.5,
                        )
                    )
                return out
            except Exception as e:
                logger.warning(f"[JapaneseProvider] analyze failed: {e}")
        # Fallback: single token
        return [
            TokenAnalysis(
                surface=text,
                lemma=text,
                reading=self.get_reading(text),
                reading_kata=None,
                pos="UNKNOWN",
                pos_detail=None,
                inflection_type=None,
                inflection_form=None,
                provenance=Provenance.PROJECT_RULE,
                confidence=0.3,
            )
        ]

    def get_lemma(self, token: str) -> str | None:
        toks = self.analyze(token)
        return toks[0].lemma if toks else None

    def get_reading(self, token: str) -> str | None:
        if self._resolver:
            try:
                return self._resolver.to_hiragana(token)
            except Exception:
                pass
        return None

    def get_pos(self, token: str) -> str | None:
        toks = self.analyze(token)
        return toks[0].pos if toks else None

    def normalize(self, text: str) -> str:
        if not text:
            return ""
        t = text.strip()
        # NFKC-ish: full-width spaces/punct
        t = re.sub(r"[。！？、\s\!\?\,\.\u3000]+", "", t)
        # Hiragana normalize optional (keep kanji, just strip)
        return t

    def resolve_dictionary_form(self, token: str) -> str | None:
        return self.get_lemma(token)

    def lookup(self, lemma: str) -> LexicalEntry | None:
        # Minimal lexical lookup: uses sudachi pos + reading, no giant dict
        # For honorific info, delegate to Keigo knowledge (small rules) elsewhere
        toks = self.analyze(lemma)
        if not toks:
            return None
        t = toks[0]
        # Detect verb class via existing conjugation engine heuristic
        verb_class = None
        if t.pos == "動詞":
            try:
                from app.domains.reflex.conjugation_engine import JapaneseConjugationEngine

                ce = JapaneseConjugationEngine()
                vc = ce.identify_verb_class(lemma)
                verb_class = vc.value
            except Exception:
                verb_class = None
        return LexicalEntry(
            lemma=t.lemma,
            reading=t.reading,
            pos=t.pos,
            verb_class=verb_class,
            semantic_category=None,
            honorific_info=None,
            source="sudachi+pykakasi",
            confidence=t.confidence,
            provenance=Provenance.MORPHOLOGICAL_ANALYZER,
        )


_provider_singleton: SudachiLanguageProvider | None = None


def get_language_provider() -> JapaneseLanguageResourceProvider:
    global _provider_singleton
    if _provider_singleton is None:
        _provider_singleton = SudachiLanguageProvider()
    return _provider_singleton
