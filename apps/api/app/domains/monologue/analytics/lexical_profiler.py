"""LexicalProfiler §28-31 via provider abstraction, graceful fallback."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any


class JapaneseLexicalResourceProvider:
    """Provider abstraction (§29/81) — replaceable, not giant DB."""

    def lookup_frequency(self, word: str) -> float | None: ...
    def lookup_difficulty(self, word: str) -> str | None: ...
    def lookup_register(self, word: str) -> str | None: ...
    def lookup_jlpt_estimate(self, word: str) -> str | None: ...
    def lookup_domain(self, word: str) -> str | None: ...


class LexicalProfiler:
    def __init__(self, provider: JapaneseLexicalResourceProvider | None = None):
        self.provider = provider
        if provider is None:
            # lazy try to use existing lexical_provider
            try:
                from app.domains.japanese.lexical_provider import get_lexical_provider

                self.provider = get_lexical_provider()  # type: ignore
            except Exception:
                self.provider = None
        try:
            from app.domains.japanese.provider import get_language_provider

            self.lang = get_language_provider()
        except Exception:
            self.lang = None

    def analyze(self, transcript: str) -> dict:
        # Tokenize via language provider
        lemmas: list[str] = []
        surfaces: list[str] = []
        if self.lang:
            try:
                toks = self.lang.analyze(transcript)
                lemmas = [t.lemma for t in toks if t.lemma]
                surfaces = [t.surface for t in toks]
            except Exception:
                pass
        if not lemmas:
            # fallback: regex tokens
            lemmas = re.findall(r"[一-龯ぁ-んァ-ン]+|\w+", transcript)
            surfaces = lemmas

        if not lemmas:
            return {
                "unique_lemmas": 0,
                "type_token_ratio": 0.0,
                "mattr": 0.0,
                "content_word_variety": 0.0,
                "repetition_clusters": [],
                "frequency_profile": {"basic": 0, "intermediate": 0, "advanced": 0, "specialized": 0},
                "jlpt_approx": {},
            }

        total = len(lemmas)
        uniq = len(set(lemmas))
        ttr = round(uniq / max(1, total), 3)

        # MATTR: moving average TTR window 20
        window = 20
        if total <= window:
            mattr = ttr
        else:
            windows = [lemmas[i : i + window] for i in range(total - window + 1)]
            mattrs = [len(set(w)) / window for w in windows]
            mattr = round(sum(mattrs) / max(1, len(mattrs)), 3)

        # Content word variety: non-particle variety
        content_lemmas = []
        if self.lang:
            try:
                toks = self.lang.analyze(transcript)
                content_lemmas = [t.lemma for t in toks if t.pos not in ("助詞", "助動詞", "記号", "補助記号")]
            except Exception:
                content_lemmas = lemmas
        else:
            content_lemmas = [l for l in lemmas if l not in {"は", "が", "を", "に", "で", "と", "の", "です", "ます"}]
        cw_uniq = len(set(content_lemmas))
        cw_variety = round(cw_uniq / max(1, len(content_lemmas)), 3) if content_lemmas else 0.0

        # Repetition clusters: scaled threshold (avoid flagging short speech)
        cnt = Counter(lemmas)
        rep_threshold = max(3, int(total * 0.12))
        clusters = [{"lemma": k, "count": v} for k, v in cnt.items() if v >= rep_threshold]
        # phrase repetition: bigrams
        bigrams = ["".join(lemmas[i : i + 2]) for i in range(len(lemmas) - 1)]
        bcnt = Counter(bigrams)
        bigram_thresh = max(3, int(len(bigrams) * 0.08)) if bigrams else 3
        for k, v in bcnt.items():
            if v >= bigram_thresh and k not in [c["lemma"] for c in clusters]:
                clusters.append({"phrase": k, "count": v})

        # Frequency profile via provider (graceful fallback)
        profile = {"basic": 0, "intermediate": 0, "advanced": 0, "specialized": 0}
        jlpt = {}
        if self.provider:
            for lemma in set(lemmas):
                try:
                    # try generic lookup
                    lvl = None
                    if hasattr(self.provider, "frequency"):
                        freq = self.provider.frequency(lemma)  # type: ignore
                        if freq is not None:
                            if freq > 1e-4:
                                lvl = "basic"
                            elif freq > 1e-5:
                                lvl = "intermediate"
                            elif freq > 1e-6:
                                lvl = "advanced"
                            else:
                                lvl = "specialized"
                    if lvl:
                        profile[lvl] += 1
                    # JLPT estimate if available
                    if hasattr(self.provider, "lookup_jlpt_estimate"):
                        jl = self.provider.lookup_jlpt_estimate(lemma)  # type: ignore
                        if jl:
                            jlpt[jl] = jlpt.get(jl, 0) + 1
                except Exception:
                    continue
        else:
            # No lexical provider — hard fail per user choice: do not mock levels
            pass  # keep profile zeros

        lexical_available = self.provider is not None
        # Top-level flag (not inside frequency_profile) for UI Low confidence badge
        return {
            "unique_lemmas": uniq,
            "type_token_ratio": ttr,
            "mattr": mattr,
            "content_word_variety": cw_variety,
            "repetition_clusters": clusters[:8],
            "frequency_profile": profile,
            "jlpt_approx": jlpt,
            "total_tokens": total,
            "provider_available": lexical_available,
        }
