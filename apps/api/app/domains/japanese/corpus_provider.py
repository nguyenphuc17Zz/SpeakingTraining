"""JapaneseCorpusProvider — pluggable frequency/collocation abstraction."""

from __future__ import annotations

from typing import Protocol

from app.domains.japanese.lexical_provider import get_lexical_provider


class JapaneseCorpusProvider(Protocol):
    def frequency(self, word: str, register: str | None = None) -> float | None: ...
    def is_common(self, word: str, threshold: float = 1e-6) -> bool: ...
    def collocations(self, word: str) -> list[str]: ...


class WordfreqCorpusProvider:
    def frequency(self, word: str, register: str | None = None) -> float | None:
        return get_lexical_provider().frequency(word)

    def is_common(self, word: str, threshold: float = 1e-6) -> bool:
        return get_lexical_provider().is_common(word, threshold)

    def collocations(self, word: str) -> list[str]:
        return []


def get_corpus_provider() -> JapaneseCorpusProvider:
    return WordfreqCorpusProvider()
