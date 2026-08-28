"""KeigoTransformationEngine — deterministic transformation with limited overrides, not giant dict.

Uses irregular overrides + rule-based generation (o~ni naru, o~suru, etc.) + lexical provider.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.domains.japanese.lexical_provider import KEIGO_IRREGULAR_OVERRIDES, get_lexical_provider
from app.domains.japanese.provider import get_language_provider
from app.domains.keigo.double_keigo import DoubleKeigoAnalyzer
from app.domains.keigo.social_context import Register, SocialContext
from app.domains.keigo.uchi_soto import UchiSotoResolver


@dataclass
class AnswerCandidate:
    text: str
    grammatical_validity: bool = True
    semantic_validity: bool = True
    register_fit: bool = True
    context_fit: bool = True
    naturalness: float = 0.85  # 0-1
    confidence: float = 0.85
    source: str = "rule"
    provenance: str = "project_rule"


@dataclass
class KeigoTransformationResult:
    source: str
    target_register: Register
    candidates: list[AnswerCandidate] = field(default_factory=list)
    canonical: str | None = None
    accepted: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    analysis: dict[str, Any] = field(default_factory=dict)


class KeigoTransformationEngine:
    """Deterministic keigo transformation engine (small overrides + rules)."""

    def __init__(self):
        self.lex = get_lexical_provider()
        self.lang = get_language_provider()
        self.uchi = UchiSotoResolver()
        self.double_analyzer = DoubleKeigoAnalyzer()

    def transform(self, source: str, target: Register, ctx: SocialContext | None = None) -> KeigoTransformationResult:
        # Analyze source
        tokens = self.lang.analyze(source)
        # Find main verb lemma (first verb)
        verb_token = next((t for t in tokens if t.pos == "動詞"), None)
        lemma = verb_token.lemma if verb_token else source.strip()
        reading = verb_token.reading if verb_token else None

        # Check irregular overrides
        overrides = KEIGO_IRREGULAR_OVERRIDES.get(lemma) or KEIGO_IRREGULAR_OVERRIDES.get(source.strip())
        candidates: list[AnswerCandidate] = []
        canonical: str | None = None

        if target == Register.TAMEGUCHI:
            # Casual: dictionary or plain
            # For simplicity, if source contains です/ます, strip to plain
            casual = self._to_casual(source, lemma)
            candidates.append(AnswerCandidate(text=casual, source="rule", provenance="project_rule", naturalness=0.9, confidence=0.85))
            canonical = casual
        elif target == Register.POLITE:
            polite = self._to_teineigo(source, lemma, overrides)
            candidates.append(AnswerCandidate(text=polite, source="rule", provenance="project_rule"))
            canonical = polite
            # Alternative: long polite
            if polite.endswith("します") and "いたし" not in polite:
                alt = polite.replace("します", "いたします")
                candidates.append(AnswerCandidate(text=alt, source="rule", provenance="project_rule", naturalness=0.85))
        elif target == Register.BUSINESS_POLITE:
            # Similar to polite but with bikago
            bp = self._to_business_polite(source, lemma, overrides)
            candidates.append(AnswerCandidate(text=bp, source="rule"))
            canonical = bp
        elif target == Register.BUSINESS_KEIGO:
            # Determine direction via SocialContext if provided
            direction = None
            if ctx:
                d = self.uchi.resolve_direction(ctx)
                if d.should_use_sonkeigo:
                    direction = "sonkeigo"
                elif d.should_use_kenjougo:
                    direction = "kenjougo"
                else:
                    direction = "teineigo"
            # If no ctx, infer from source pattern: if source mentions customer/boss, sonkeigo
            if not direction:
                direction = self._infer_direction_from_text(source)
            if direction == "sonkeigo":
                form = self._to_sonkeigo(source, lemma, overrides)
            elif direction == "kenjougo":
                form = self._to_kenjougo(source, lemma, overrides)
            else:
                form = self._to_teineigo(source, lemma, overrides)
            candidates.append(AnswerCandidate(text=form, source="rule" if overrides else "lexical_resource", provenance="project_rule" if overrides else "lexical_resource"))
            canonical = form
            # Alternative for business keigo: add more humble variant
            if "いたし" in form:
                alt2 = form.replace("いたし", "させていただき")
                candidates.append(AnswerCandidate(text=alt2, source="rule", naturalness=0.8))
        elif target == Register.VERY_FORMAL:
            vf = self._to_very_formal(source, lemma, overrides)
            candidates.append(AnswerCandidate(text=vf, source="rule"))
            canonical = vf

        # Deduplicate and set accepted
        seen = set()
        uniq: list[AnswerCandidate] = []
        for c in candidates:
            if c.text not in seen:
                # Check double keigo
                dk = self.double_analyzer.analyze(c.text)
                if dk["status"] == "generally_inappropriate":
                    c.naturalness = min(c.naturalness, 0.55)
                    c.confidence = min(c.confidence, 0.6)
                uniq.append(c)
                seen.add(c.text)
        candidates = uniq
        accepted = [c.text for c in candidates]
        # Limit to 2-3 canonical
        canonical = candidates[0].text if candidates else None

        return KeigoTransformationResult(
            source=source,
            target_register=target,
            candidates=candidates,
            canonical=canonical,
            accepted=accepted,
            alternatives=[c.text for c in candidates[1:]],
            analysis={"lemma": lemma, "reading": reading, "overrides": bool(overrides), "tokens": [t.surface for t in tokens]},
        )

    def _to_casual(self, source: str, lemma: str) -> str:
        # Strip desu/masu
        t = source.strip()
        t = re.sub(r"です。?$", "だ。", t)
        t = re.sub(r"ます。?$", "る。", t)
        t = re.sub(r"でした。?$", "だった。", t)
        t = re.sub(r"ました。?$", "た。", t)
        return t

    def _to_teineigo(self, source: str, lemma: str, overrides: dict | None) -> str:
        if overrides and "teineigo" in overrides and overrides["teineigo"] != "—":
            # For single verb, replace
            if lemma in source:
                return source.replace(lemma, overrides["teineigo"])
            return overrides["teineigo"]
        # General rule: verb + ます
        # Use conjugation engine for godan/ichidan masu
        try:
            from app.domains.reflex.conjugation_engine import JapaneseConjugationEngine

            ce = JapaneseConjugationEngine()
            # Try to get masu via teineigo: for verb, masu is essentially polite
            # Use internal: if ichidan, stem+ます; if godan, i-row+ます
            vc = ce.identify_verb_class(lemma)
            if vc.value == "ichidan":
                stem = lemma[:-1] if lemma.endswith("る") else lemma
                masu = stem + "ます"
                if lemma in source:
                    return source.replace(lemma, masu)
                return masu
            elif vc.value == "godan":
                # i-row
                ending = lemma[-1]
                mapping = {"う": "い", "く": "き", "ぐ": "ぎ", "す": "し", "つ": "ち", "ぬ": "に", "ぶ": "び", "む": "み", "る": "り"}
                if ending in mapping:
                    masu = lemma[:-1] + mapping[ending] + "ます"
                    if lemma in source:
                        return source.replace(lemma, masu)
                    return masu
        except Exception:
            pass
        # Fallback: append ます if ends with る/う etc
        return source + "ます" if not source.endswith("ます") else source

    def _to_business_polite(self, source: str, lemma: str, overrides: dict | None) -> str:
        # Adds お/ご prefix where appropriate (bikago) + teineigo
        teineigo = self._to_teineigo(source, lemma, overrides)
        # Simple bikago: if noun before verb, add お
        # For demo, just return teineigo
        return teineigo

    def _to_sonkeigo(self, source: str, lemma: str, overrides: dict | None) -> str:
        if overrides and "sonkeigo" in overrides and overrides["sonkeigo"] != "—":
            if lemma in source:
                return source.replace(lemma, overrides["sonkeigo"])
            return overrides["sonkeigo"]
        # Rule: お + stem + になる (for godan/ichidan)
        try:
            from app.domains.reflex.conjugation_engine import JapaneseConjugationEngine

            ce = JapaneseConjugationEngine()
            vc = ce.identify_verb_class(lemma)
            if lemma.endswith("する"):
                base = lemma[:-2]
                son = f"ご{base}になる" if base else "なさる"
                if lemma in source:
                    return source.replace(lemma, son)
                return son
            # General: お + masu stem + になる
            masu = self._to_teineigo(lemma, lemma, None)
            # masu ends with ます, strip to stem
            if masu.endswith("ます"):
                stem = masu[:-2]
                # stem is e.g. かき, たべ
                son = f"お{stem}になる"
                if lemma in source:
                    return source.replace(lemma, son)
                return son
        except Exception:
            pass
        return f"お{lemma}になる"

    def _to_kenjougo(self, source: str, lemma: str, overrides: dict | None) -> str:
        if overrides and "kenjougo" in overrides and overrides["kenjougo"] != "—":
            if lemma in source:
                return source.replace(lemma, overrides["kenjougo"])
            return overrides["kenjougo"]
        # Rule: お + stem + する / いたす
        try:
            masu = self._to_teineigo(lemma, lemma, None)
            if masu.endswith("ます"):
                stem = masu[:-2]
                ken = f"お{stem}する"
                if lemma in source:
                    return source.replace(lemma, ken)
                return ken
        except Exception:
            pass
        return f"お{lemma}する"

    def _to_very_formal(self, source: str, lemma: str, overrides: dict | None) -> str:
        ken = self._to_kenjougo(source, lemma, overrides)
        # Very formal adds いたす instead of する
        return ken.replace("する", "いたす") if ken.endswith("する") else ken + "いたす"

    def _infer_direction_from_text(self, text: str) -> str:
        # Heuristic: if text mentions 客様, 社長, 部長, 先生 → sonkeigo
        soto_keywords = ["客様", "お客様", "社長", "部長", "先生", "課長", "先方"]
        for kw in soto_keywords:
            if kw in text:
                return "sonkeigo"
        # If mentions 私, 弊社, 当社 → kenjougo
        uchi_keywords = ["私", "弊社", "当社", "わたくし"]
        for kw in uchi_keywords:
            if kw in text:
                return "kenjougo"
        return "teineigo"

    def validate(self, user_text: str, expected_candidates: list[str]) -> dict:
        # Normalize both via language provider
        norm_user = self.lang.normalize(user_text)
        for cand in expected_candidates:
            norm_cand = self.lang.normalize(cand)
            if norm_user == norm_cand:
                return {"is_correct": True, "matched": cand, "confidence": 0.95}
            # Allow hiragana equivalence
            hira_user = self.lang.get_reading(user_text) or norm_user
            hira_cand = self.lang.get_reading(cand) or norm_cand
            if hira_user == hira_cand:
                return {"is_correct": True, "matched": cand, "confidence": 0.88}
        return {"is_correct": False, "matched": None, "confidence": 0.7}
