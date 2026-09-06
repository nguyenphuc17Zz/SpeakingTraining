"""LexicalProfiler §28-31 via provider abstraction, graceful fallback."""

from __future__ import annotations

import re
from collections import Counter


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
        if self.lang:
            try:
                toks = self.lang.analyze(transcript)
                lemmas = [t.lemma for t in toks if t.lemma]
                [t.surface for t in toks]
            except Exception:
                pass
        if not lemmas:
            # fallback: regex tokens
            lemmas = re.findall(r"[一-龯ぁ-んァ-ン]+|\w+", transcript)

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
            content_lemmas = [lemma for lemma in lemmas if lemma not in {"は", "が", "を", "に", "で", "と", "の", "です", "ます"}]
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

        # MTLD (Measure of Textual Lexical Diversity - McCarthy & Jarvis 2010)
        mtld = self.compute_mtld(lemmas)

        # HD-D (Hypergeometric Distribution Diversity - McCarthy & Jarvis 2007)
        hdd = self.compute_hdd(lemmas)

        # Diversity classification based on SOTA benchmarks
        if mtld >= 70.0:
            diversity_level = "rich"
        elif mtld >= 45.0:
            diversity_level = "moderate"
        elif mtld >= 25.0:
            diversity_level = "basic"
        else:
            diversity_level = "repetitive"

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
            "mtld": mtld,
            "hdd": hdd,
            "lexical_diversity_rating": diversity_level,
            "content_word_variety": cw_variety,
            "repetition_clusters": clusters[:8],
            "frequency_profile": profile,
            "jlpt_approx": jlpt,
            "total_tokens": total,
            "provider_available": lexical_available,
        }

    @staticmethod
    def _mtld_factor_count(tokens: list[str], threshold: float = 0.72) -> float:
        """Computes sequential factor count for a single direction."""
        if not tokens:
            return 0.0
        factors = 0.0
        types: set[str] = set()
        token_count = 0

        for tok in tokens:
            types.add(tok)
            token_count += 1
            current_ttr = len(types) / token_count
            if current_ttr <= threshold:
                factors += 1.0
                types.clear()
                token_count = 0

        # Partial factor for trailing segment
        if token_count > 0:
            final_ttr = len(types) / token_count
            if final_ttr < 1.0 and (1.0 - threshold) > 1e-6:
                factors += (1.0 - final_ttr) / (1.0 - threshold)
            else:
                factors += 0.1

        return max(factors, 0.1)

    @classmethod
    def compute_mtld(cls, tokens: list[str], threshold: float = 0.72) -> float:
        """
        Calculates bi-directional Measure of Textual Lexical Diversity (MTLD).
        McCarthy & Jarvis (2010). Length-independent lexical diversity metric.
        """
        n = len(tokens)
        if n < 2:
            return 0.0
        forward_factors = cls._mtld_factor_count(tokens, threshold)
        reverse_factors = cls._mtld_factor_count(list(reversed(tokens)), threshold)
        avg_factors = (forward_factors + reverse_factors) / 2.0
        return round(float(n) / max(avg_factors, 0.01), 2)

    @staticmethod
    def compute_hdd(tokens: list[str], sample_size: int = 35) -> float:
        """
        Calculates Hypergeometric Distribution Diversity (HD-D) index (McCarthy & Jarvis 2007).
        Evaluates the probability of observing each type in a random hypergeometric draw of size s.
        """
        n = len(tokens)
        if n < 4:
            return 0.0

        s = min(sample_size, n)
        counts = Counter(tokens)
        hdd_sum = 0.0

        for count in counts.values():
            # If token frequency is large enough that (n - count) < s, prob of drawing at least one is 1.0
            if n - count < s:
                prob = 1.0
            else:
                # Compute prod_{i=0}^{s-1} (n - count - i) / (n - i)
                prob_zero = 1.0
                for i in range(s):
                    prob_zero *= (n - count - i) / (n - i)
                prob = 1.0 - prob_zero
            hdd_sum += prob

        # Normalized HD-D: expected types drawn divided by sample size s
        return round(hdd_sum / max(1.0, float(s)), 3)
