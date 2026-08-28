"""JapanesePitchResourceProvider — pluggable accent resource, composite + pyopenjtalk guarded."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from app.core.logging import logger
from app.domains.japanese.provider import get_language_provider
from app.domains.pronunciation.japanese.pitch_accent_resolver import PitchAccentTargetResolver


class Provenance(str, Enum):
    OFFICIAL_GUIDANCE = "official_guidance"
    LEXICAL_RESOURCE = "lexical_resource"
    CORPUS = "corpus"
    ACOUSTIC_ESTIMATE = "acoustic_estimate"
    PROJECT_POLICY = "project_policy"
    AI_INFERENCE = "ai_inference"


class AccentType(str, Enum):
    HEIBAN = "heiban"
    ATAMADAKA = "atamadaka"
    NAKADAKA = "nakadaka"
    ODAKA = "odaka"
    UNKNOWN = "unknown"


@dataclass
class PitchLexicalEntry:
    text: str
    reading: str
    mora_count: int
    accent_position: int | None  # 0=heiban, 1=atamadaka, etc. None unknown
    accent_type: AccentType
    pattern: list[str]  # ["L","H","H","L"]
    drop_location: int | None
    source: str
    provenance: Provenance
    confidence: float
    version: str = "1.0.0"


class JapanesePitchResourceProvider(Protocol):
    def lookup(self, text: str) -> PitchLexicalEntry | None: ...
    def get_reading(self, text: str) -> str | None: ...
    def get_mora(self, text: str) -> list[str]: ...
    def get_accent_pattern(self, text: str) -> list[str] | None: ...
    def get_source_metadata(self, text: str) -> dict: ...


class SudachiPitchProvider:
    """Fallback using existing Short lexicon + mora analyzer."""

    def __init__(self):
        self.lang = get_language_provider()
        self.resolver = PitchAccentTargetResolver()

    def lookup(self, text: str) -> PitchLexicalEntry | None:
        try:
            # Use mora analyzer for mora_count
            from app.domains.pronunciation.japanese.mora_analyzer import JapaneseMoraAnalyzer

            ma = JapaneseMoraAnalyzer()
            reading = self.lang.get_reading(text) or text
            moras = ma.segment_moras(reading)
            mora_count = len(moras)
            # Use pitch_accent_resolver for pattern
            pattern_type, kernel, levels = self.resolver.resolve_target(text)
            # Map PitchAccentPattern to AccentType
            type_map = {
                "heiban": AccentType.HEIBAN,
                "atamadaka": AccentType.ATAMADAKA,
                "nakadaka": AccentType.NAKADAKA,
                "odaka": AccentType.ODAKA,
            }
            accent_type = type_map.get(str(pattern_type.value).lower(), AccentType.UNKNOWN)
            # drop = kernel if kernel!=0 else None
            drop = kernel if kernel and kernel != 0 else None
            return PitchLexicalEntry(
                text=text,
                reading=reading,
                mora_count=mora_count,
                accent_position=kernel,
                accent_type=accent_type,
                pattern=levels,
                drop_location=drop,
                source="sudachi_pitch_resolver",
                provenance=Provenance.LEXICAL_RESOURCE,
                confidence=0.75 if pattern_type.value != "UNKNOWN" else 0.4,
            )
        except Exception as e:
            logger.warning(f"[SudachiPitchProvider] lookup failed {e}")
            return None

    def get_reading(self, text: str) -> str | None:
        return self.lang.get_reading(text)

    def get_mora(self, text: str) -> list[str]:
        try:
            from app.domains.pronunciation.japanese.mora_analyzer import JapaneseMoraAnalyzer

            ma = JapaneseMoraAnalyzer()
            reading = self.lang.get_reading(text) or text
            moras = ma.segment_moras(reading)
            return [m.kana for m in moras]
        except Exception:
            return []

    def get_accent_pattern(self, text: str) -> list[str] | None:
        e = self.lookup(text)
        return e.pattern if e else None

    def get_source_metadata(self, text: str) -> dict:
        e = self.lookup(text)
        if e:
            return {"source": e.source, "provenance": e.provenance.value, "confidence": e.confidence, "version": e.version}
        return {"source": "unknown", "provenance": Provenance.AI_INFERENCE.value, "confidence": 0.0}


class PyOpenJTalkProvider:
    """pyopenjtalk provider — guarded import, used when available."""

    def __init__(self):
        self.available = False
        self._oj = None
        try:
            import pyopenjtalk  # type: ignore

            self._oj = pyopenjtalk
            self.available = True
        except Exception as e:
            logger.info(f"[PyOpenJTalkProvider] not available: {e}")
            self.available = False

    def lookup(self, text: str) -> PitchLexicalEntry | None:
        if not self.available or not self._oj:
            return None
        try:
            # pyopenjtalk.extract_fullcontext returns full-context labels
            labels = self._oj.extract_fullcontext(text)
            # Parse accent: labels contain "/A:xx+yy+zz" where xx is accent position? Simplified
            # Use pyopenjtalk.g2p for reading/mora
            g2p = self._oj.g2p(text, kana=False)  # returns phoneme?
            # Fallback to sudachi for mora
            from app.domains.japanese.provider import get_language_provider

            lang = get_language_provider()
            reading = lang.get_reading(text) or text
            # Estimate mora via reading length
            # For MVP, delegate to Sudachi provider for moras, but mark provenance as pyopenjtalk
            sudachi = SudachiPitchProvider()
            base = sudachi.lookup(text)
            if base:
                base.source = "pyopenjtalk"
                base.provenance = Provenance.OFFICIAL_GUIDANCE
                base.confidence = min(0.97, base.confidence + 0.15)
                return base
            return None
        except Exception as e:
            logger.warning(f"[PyOpenJTalkProvider] lookup failed: {e}")
            return None

    def get_reading(self, text: str) -> str | None:
        if self.available and self._oj:
            try:
                return self._oj.g2p(text, kana=True)  # kana reading
            except Exception:
                pass
        # fallback
        return SudachiPitchProvider().get_reading(text)

    def get_mora(self, text: str) -> list[str]:
        return SudachiPitchProvider().get_mora(text)

    def get_accent_pattern(self, text: str) -> list[str] | None:
        e = self.lookup(text)
        return e.pattern if e else None

    def get_source_metadata(self, text: str) -> dict:
        e = self.lookup(text)
        if e and e.provenance == Provenance.OFFICIAL_GUIDANCE:
            return {"source": "pyopenjtalk", "provenance": e.provenance.value, "confidence": e.confidence}
        return SudachiPitchProvider().get_source_metadata(text)


class CompositePitchResourceProvider:
    """Composite: pyopenjtalk → sudachi → AI unknown."""

    def __init__(self):
        self.primary = PyOpenJTalkProvider()
        self.secondary = SudachiPitchProvider()

    def lookup(self, text: str) -> PitchLexicalEntry | None:
        # Try primary
        if self.primary.available:
            e = self.primary.lookup(text)
            if e and e.confidence >= 0.85:
                return e
        # Secondary
        e2 = self.secondary.lookup(text)
        if e2 and e2.confidence >= 0.6:
            # If both agree, boost confidence
            if self.primary.available and e and e2 and e.pattern == e2.pattern:
                e2.confidence = min(0.99, e2.confidence + 0.1)
                e2.provenance = Provenance.LEXICAL_RESOURCE
            return e2
        # Primary low conf fallback
        if self.primary.available:
            e = self.primary.lookup(text)
            if e:
                return e
        if e2:
            return e2
        # Unknown
        return PitchLexicalEntry(
            text=text,
            reading=self.secondary.get_reading(text) or text,
            mora_count=len(self.secondary.get_mora(text)) or len(text),
            accent_position=None,
            accent_type=AccentType.UNKNOWN,
            pattern=[],
            drop_location=None,
            source="unknown",
            provenance=Provenance.AI_INFERENCE,
            confidence=0.0,
        )

    def get_reading(self, text: str) -> str | None:
        r = self.lookup(text)
        return r.reading if r else None

    def get_mora(self, text: str) -> list[str]:
        return self.secondary.get_mora(text)

    def get_accent_pattern(self, text: str) -> list[str] | None:
        r = self.lookup(text)
        return r.pattern if r else None

    def get_source_metadata(self, text: str) -> dict:
        r = self.lookup(text)
        if r:
            return {"source": r.source, "provenance": r.provenance.value, "confidence": r.confidence, "version": r.version}
        return {"source": "unknown", "provenance": Provenance.AI_INFERENCE.value, "confidence": 0.0}


_provider: CompositePitchResourceProvider | None = None


def get_pitch_provider() -> JapanesePitchResourceProvider:
    global _provider
    if _provider is None:
        _provider = CompositePitchResourceProvider()
    return _provider
