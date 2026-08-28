"""JapaneseConjugationEngine — deterministic conjugation + acceptable variants.

Covers 12 forms: 辞書形, ない形, た形, て形, 可能形, 受身形, 使役形, 使役受身形, 命令形, 意向形, ば形, たら形
Supports ichidan / godan / irregular (する/来る) + 行く special handling.
No LLM in core; AI fallback only for ambiguity via AIRouter outside this engine.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class VerbClass(str, Enum):
    ICHIDAN = "ichidan"
    GODAN = "godan"
    SURU = "suru"
    KURU = "kuru"
    IRREGULAR = "irregular"


class ConjugationForm(str, Enum):
    DICTIONARY = "dictionary"      # 辞書形
    NAI = "nai"                    # ない形
    TA = "ta"                      # た形
    TE = "te"                      # て形
    POTENTIAL = "potential"        # 可能形
    PASSIVE = "passive"            # 受身形
    CAUSATIVE = "causative"        # 使役形
    CAUSATIVE_PASSIVE = "causative_passive"  # 使役受身形
    IMPERATIVE = "imperative"      # 命令形
    VOLITIONAL = "volitional"      # 意向形
    BA = "ba"                      # ば形
    TARA = "tara"                  # たら形


# Godan ending maps: dict[ending_kana] -> transforms
# For godan, we map the kana ending to different stems
GODAN_A_MAP = {"う": "わ", "く": "か", "ぐ": "が", "す": "さ", "つ": "た", "ぬ": "な", "ぶ": "ば", "む": "ま", "る": "ら"}
GODAN_I_MAP = {"う": "い", "く": "き", "ぐ": "ぎ", "す": "し", "つ": "ち", "ぬ": "に", "ぶ": "び", "む": "み", "る": "り"}
GODAN_E_MAP = {"う": "え", "く": "け", "ぐ": "げ", "す": "せ", "つ": "て", "ぬ": "ね", "ぶ": "べ", "む": "め", "る": "れ"}
GODAN_O_MAP = {"う": "お", "く": "こ", "ぐ": "ご", "す": "そ", "つ": "と", "ぬ": "の", "ぶ": "ぼ", "む": "も", "る": "ろ"}

# Special 行く past/te forms
IKU_EXCEPTIONS = {"行く", "いく", "イク"}

# Common ichidan verbs for detection (heuristic fallback)
ICHIDAN_ENDINGS = ("える", "られる", "いる", "きる", "みる", "じる", "ける", "げる", "ける", "てる", "でる", "ねる", "れる")


@dataclass
class ConjugationTarget:
    """Result of conjugation generation."""

    verb: str  # original dictionary form
    verb_class: VerbClass
    form: ConjugationForm
    canonical: str
    accepted: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    variant_notes: list[str] = field(default_factory=list)
    reading: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "verb": self.verb,
            "verb_class": self.verb_class.value,
            "form": self.form.value,
            "canonical": self.canonical,
            "accepted": self.accepted,
            "alternatives": self.alternatives,
            "variant_notes": self.variant_notes,
            "reading": self.reading,
        }


class JapaneseConjugationEngine:
    """Deterministic Japanese verb conjugation engine."""

    # Minimal verb class database for common verbs
    KNOWN_GODAN = {
        "書く", "かく", "行く", "いく", "話す", "はなす", "買う", "かう",
        "待つ", "まつ", "死ぬ", "しぬ", "遊ぶ", "あそぶ", "読む", "よむ",
        "走る", "はしる", "切る", "きる", "知る", "しる", "入る", "はいる",
        "帰る", "かえる", "要る", "いる", "滑る", "すべる", "握る", "にぎる",
        "立つ", "たつ", "持つ", "もつ", "勝つ", "かつ", "飲む", "のむ",
        "読む", "よむ", "呼ぶ", "よぶ", "飛ぶ", "とぶ", "泳ぐ", "およぐ",
        "急ぐ", "いそぐ", "話す", "はなす", "出す", "だす", "消す", "けす",
        "買う", "かう", "会う", "あう", "使う", "つかう", "習う", "ならう",
    }
    KNOWN_ICHIDAN = {
        "食べる", "たべる", "見る", "みる", "起きる", "おきる", "寝る", "ねる",
        "いる", "着る", "きる", "信じる", "しんじる", "感じる", "かんじる",
        "教える", "おしえる", "覚える", "おぼえる", "出る", "でる", "借りる", "かりる",
        "考える", "かんがえる", "見せる", "みせる", "開ける", "あける", "閉める", "しめる",
        "食べられる", "たべられる",  # already conjugated but treat as base for test
    }

    def identify_verb_class(self, verb: str) -> VerbClass:
        v = verb.strip()
        if v in ("する", "為る") or v.endswith("する"):
            return VerbClass.SURU
        if v in ("来る", "くる", "来る", "クル") or v.endswith("来る") or v.endswith("くる"):
            return VerbClass.KURU
        if v in self.KNOWN_GODAN:
            return VerbClass.GODAN
        if v in self.KNOWN_ICHIDAN:
            return VerbClass.ICHIDAN
        # Heuristic: ichidan ends with える/いる with preceding kana containing e/i sound
        if v.endswith("る"):
            # Check if preceding char is e-row or i-row
            if len(v) >= 2:
                # Simple heuristic: if ends with える/いる etc, likely ichidan unless known godan
                pre = v[-2]
                # e-row / i-row kana
                e_row = set("えけげせぜてでねへべぺめれ")
                i_row = set("いきぎしじちぢにひびぴみり")
                if pre in e_row or pre in i_row:
                    # Check godan known exceptions (e.g., 帰る, 切る)
                    if v not in self.KNOWN_GODAN:
                        return VerbClass.ICHIDAN
            return VerbClass.GODAN
        # Default to godan for single kana verbs like 行く
        if len(v) == 1 or v[-1] in GODAN_A_MAP:
            return VerbClass.GODAN
        return VerbClass.GODAN

    def _godan_stem(self, verb: str, target_row: str) -> str:
        ending = verb[-1]
        mapping = {
            "a": GODAN_A_MAP,
            "i": GODAN_I_MAP,
            "e": GODAN_E_MAP,
            "o": GODAN_O_MAP,
        }[target_row]
        replaced = mapping.get(ending, ending)
        return verb[:-1] + replaced

    def _godan_te_ta(self, verb: str) -> tuple[str, str]:
        """Returns (te_form, ta_form) for godan verbs with sound changes."""
        if verb in IKU_EXCEPTIONS or verb == "行く":
            return verb[:-1] + "って", verb[:-1] + "った"
        ending = verb[-1]
        stem = verb[:-1]
        if ending in ("う", "つ", "る"):
            return stem + "って", stem + "った"
        if ending in ("む", "ぶ", "ぬ"):
            return stem + "んで", stem + "んだ"
        if ending == "く":
            return stem + "いて", stem + "いた"
        if ending == "ぐ":
            return stem + "いで", stem + "いだ"
        if ending == "す":
            return stem + "して", stem + "した"
        return stem + "って", stem + "った"

    def conjugate(self, verb: str, form: ConjugationForm | str) -> ConjugationTarget:
        if isinstance(form, str):
            # Allow Japanese labels or enum values
            form_map = {
                "辞書形": ConjugationForm.DICTIONARY, "dictionary": ConjugationForm.DICTIONARY,
                "ない形": ConjugationForm.NAI, "ない": ConjugationForm.NAI, "nai": ConjugationForm.NAI,
                "た形": ConjugationForm.TA, "た": ConjugationForm.TA, "ta": ConjugationForm.TA,
                "て形": ConjugationForm.TE, "て": ConjugationForm.TE, "te": ConjugationForm.TE,
                "可能形": ConjugationForm.POTENTIAL, "potential": ConjugationForm.POTENTIAL, "可能": ConjugationForm.POTENTIAL,
                "受身形": ConjugationForm.PASSIVE, "passive": ConjugationForm.PASSIVE, "受身": ConjugationForm.PASSIVE,
                "使役形": ConjugationForm.CAUSATIVE, "causative": ConjugationForm.CAUSATIVE, "使役": ConjugationForm.CAUSATIVE,
                "使役受身形": ConjugationForm.CAUSATIVE_PASSIVE, "causative_passive": ConjugationForm.CAUSATIVE_PASSIVE, "使役受身": ConjugationForm.CAUSATIVE_PASSIVE, "使役受身・過去": ConjugationForm.CAUSATIVE_PASSIVE,
                "命令形": ConjugationForm.IMPERATIVE, "imperative": ConjugationForm.IMPERATIVE, "命令": ConjugationForm.IMPERATIVE,
                "意向形": ConjugationForm.VOLITIONAL, "volitional": ConjugationForm.VOLITIONAL, "意向": ConjugationForm.VOLITIONAL,
                "ば形": ConjugationForm.BA, "ba": ConjugationForm.BA, "ば": ConjugationForm.BA,
                "たら形": ConjugationForm.TARA, "tara": ConjugationForm.TARA, "たら": ConjugationForm.TARA,
            }
            form = form_map.get(form, ConjugationForm.DICTIONARY)

        vc = self.identify_verb_class(verb)
        canonical, accepted, alternatives, notes = self._generate(verb, vc, form)
        # Always include canonical in accepted
        if canonical not in accepted:
            accepted = [canonical] + accepted
        return ConjugationTarget(
            verb=verb,
            verb_class=vc,
            form=form,
            canonical=canonical,
            accepted=accepted,
            alternatives=alternatives,
            variant_notes=notes,
        )

    def _generate(self, verb: str, vc: VerbClass, form: ConjugationForm) -> tuple[str, list[str], list[str], list[str]]:
        accepted: list[str] = []
        alternatives: list[str] = []
        notes: list[str] = []

        if form == ConjugationForm.DICTIONARY:
            return verb, [verb], [], ["辞書形 = nguyên thể"]

        # SURU handling
        if vc == VerbClass.SURU:
            base = verb[:-2] if verb.endswith("する") else ""
            mapping = {
                ConjugationForm.NAI: "しない",
                ConjugationForm.TA: "した",
                ConjugationForm.TE: "して",
                ConjugationForm.POTENTIAL: "できる",
                ConjugationForm.PASSIVE: "される",
                ConjugationForm.CAUSATIVE: "させる",
                ConjugationForm.CAUSATIVE_PASSIVE: "させられる",
                ConjugationForm.IMPERATIVE: "しろ",
                ConjugationForm.VOLITIONAL: "しよう",
                ConjugationForm.BA: "すれば",
                ConjugationForm.TARA: "したら",
            }
            canon = base + mapping.get(form, verb)
            # Variants for する
            if form == ConjugationForm.CAUSATIVE_PASSIVE:
                accepted = [canon, base + "される"] if base else [canon]
                notes.append("使役受身 của する có thể rút gọn")
            elif form == ConjugationForm.PASSIVE:
                notes.append("受身 của する = される")
            elif form == ConjugationForm.IMPERATIVE:
                alternatives = [base + "せよ"] if base else []
            return canon, accepted, alternatives, notes

        # KURU handling
        if vc == VerbClass.KURU:
            # Handle 来る and compounds like 持って来る
            is_compound = verb not in ("来る", "くる") and len(verb) > 2
            base = verb[:-2] if is_compound else ""
            mapping = {
                ConjugationForm.NAI: "来ない" if not is_compound else base + "来ない",
                ConjugationForm.TA: "来た" if not is_compound else base + "来た",
                ConjugationForm.TE: "来て" if not is_compound else base + "来て",
                ConjugationForm.POTENTIAL: "来られる" if not is_compound else base + "来られる",
                ConjugationForm.PASSIVE: "来られる" if not is_compound else base + "来られる",
                ConjugationForm.CAUSATIVE: "来させる" if not is_compound else base + "来させる",
                ConjugationForm.CAUSATIVE_PASSIVE: "来させられる" if not is_compound else base + "来させられる",
                ConjugationForm.IMPERATIVE: "来い" if not is_compound else base + "来い",
                ConjugationForm.VOLITIONAL: "来よう" if not is_compound else base + "来よう",
                ConjugationForm.BA: "来れば" if not is_compound else base + "来れば",
                ConjugationForm.TARA: "来たら" if not is_compound else base + "来たら",
            }
            # Also handle hiragana variant
            if verb == "くる":
                mapping = {
                    ConjugationForm.NAI: "こない",
                    ConjugationForm.TA: "きた",
                    ConjugationForm.TE: "きて",
                    ConjugationForm.POTENTIAL: "こられる",
                    ConjugationForm.PASSIVE: "こられる",
                    ConjugationForm.CAUSATIVE: "こさせる",
                    ConjugationForm.CAUSATIVE_PASSIVE: "こさせられる",
                    ConjugationForm.IMPERATIVE: "こい",
                    ConjugationForm.VOLITIONAL: "こよう",
                    ConjugationForm.BA: "くれば",
                    ConjugationForm.TARA: "きたら",
                }
            canon = mapping.get(form, verb)
            if form == ConjugationForm.CAUSATIVE_PASSIVE:
                notes.append("来る causative-passive contracted variant こさせられる vs 来させられる")
            return canon, accepted, alternatives, notes

        # ICHIDAN
        if vc == VerbClass.ICHIDAN:
            stem = verb[:-1] if verb.endswith("る") else verb
            mapping = {
                ConjugationForm.NAI: stem + "ない",
                ConjugationForm.TA: stem + "た",
                ConjugationForm.TE: stem + "て",
                ConjugationForm.POTENTIAL: stem + "られる",
                ConjugationForm.PASSIVE: stem + "られる",
                ConjugationForm.CAUSATIVE: stem + "させる",
                ConjugationForm.CAUSATIVE_PASSIVE: stem + "させられる",
                ConjugationForm.IMPERATIVE: stem + "ろ",
                ConjugationForm.VOLITIONAL: stem + "よう",
                ConjugationForm.BA: stem + "れば",
                ConjugationForm.TARA: stem + "たら",
            }
            canon = mapping.get(form, verb)
            if form == ConjugationForm.POTENTIAL:
                # ら抜き variant
                alternatives = [stem + "れる"]
                notes.append("ら抜き言葉 (potential contraction) 可能だが canonical giữ られる")
            if form == ConjugationForm.CAUSATIVE_PASSIVE:
                # contracted
                alternatives = [stem + "される"]
                notes.append("使役受身 rút gọn: させられる → される (ichidan)")
            return canon, accepted, alternatives, notes

        # GODAN
        # stem for a-row etc
        if form == ConjugationForm.NAI:
            return self._godan_stem(verb, "a") + "ない", [], [], []
        if form == ConjugationForm.TA:
            _, ta = self._godan_te_ta(verb)
            return ta, [], [], []
        if form == ConjugationForm.TE:
            te, _ = self._godan_te_ta(verb)
            return te, [], [], []
        if form == ConjugationForm.POTENTIAL:
            canon = self._godan_stem(verb, "e") + "る"
            return canon, [], [], []
        if form == ConjugationForm.PASSIVE:
            canon = self._godan_stem(verb, "a") + "れる"
            return canon, [], [], []
        if form == ConjugationForm.CAUSATIVE:
            canon = self._godan_stem(verb, "a") + "せる"
            return canon, [], [], []
        if form == ConjugationForm.CAUSATIVE_PASSIVE:
            canon = self._godan_stem(verb, "a") + "せられる"
            contracted = self._godan_stem(verb, "a") + "される"
            accepted = [contracted]
            notes.append("使役受身 godan có 2 dạng: せられる (canonical) và される (contracted, commonly accepted)")
            return canon, accepted, [contracted], notes
        if form == ConjugationForm.IMPERATIVE:
            canon = self._godan_stem(verb, "e")
            return canon, [], [], []
        if form == ConjugationForm.VOLITIONAL:
            canon = self._godan_stem(verb, "o") + "う"
            return canon, [], [], []
        if form == ConjugationForm.BA:
            canon = self._godan_stem(verb, "e") + "ば"
            return canon, [], [], []
        if form == ConjugationForm.TARA:
            _, ta = self._godan_te_ta(verb)
            # ta ends with た/だ, tara = ta + ら but need to handle correctly: た→たら, だ→たら? Actually んだ→んだら
            if ta.endswith("た"):
                canon = ta[:-1] + "たら"
            elif ta.endswith("だ"):
                canon = ta[:-1] + "だら"
            else:
                canon = ta + "ら"
            return canon, [], [], []

        return verb, [], [], []

    def validate(self, verb: str, form: ConjugationForm | str, answer: str, normalize: bool = True) -> dict[str, Any]:
        """Validates user answer against expected conjugation.

        Returns {is_correct, canonical, accepted, matched_form, note}
        """
        target = self.conjugate(verb, form)
        ans_norm = self._normalize(answer) if normalize else answer.strip()
        ans_kana = self._to_kana(ans_norm)

        # Also normalize accepted for comparison
        accepted_norm = [self._normalize(a) for a in target.accepted]
        canonical_norm = self._normalize(target.canonical)
        alternatives_norm = [self._normalize(a) for a in target.alternatives]

        # Generate phonetic Kana variants for all accepted targets
        all_norm_variants = accepted_norm + alternatives_norm + [canonical_norm]
        all_kana_variants = [self._to_kana(v) for v in all_norm_variants]

        all_accepted = set(all_norm_variants + all_kana_variants)
        # Also accept without normalization check
        raw_accepted = set(target.accepted + target.alternatives + [target.canonical])
        is_correct = (
            ans_norm in all_accepted
            or ans_kana in all_accepted
            or answer.strip() in raw_accepted
        )
        matched = None
        if is_correct:
            # Find which form matched
            for orig in raw_accepted:
                if (
                    self._normalize(orig) == ans_norm
                    or self._to_kana(self._normalize(orig)) == ans_kana
                    or orig == answer.strip()
                ):
                    matched = orig
                    break
        return {
            "is_correct": is_correct,
            "canonical": target.canonical,
            "accepted": target.accepted,
            "alternatives": target.alternatives,
            "matched": matched or target.canonical,
            "verb_class": target.verb_class.value,
            "form": target.form.value,
            "variant_notes": target.variant_notes,
        }

    def _to_kana(self, text: str) -> str:
        """Converts common Kanji verb stems and Katakana to pure Hiragana."""
        if not text:
            return ""
        t = text
        kanji_kana_pairs = [
            ("食べる", "たべる"), ("食べ", "たべ"),
            ("見る", "みる"), ("見", "み"),
            ("行く", "いく"), ("行", "い"),
            ("書く", "かく"), ("書", "か"),
            ("読む", "よむ"), ("読", "よ"),
            ("飲む", "のむ"), ("飲", "の"),
            ("話す", "はなす"), ("話", "はな"),
            ("買う", "かう"), ("買", "か"),
            ("待つ", "まつ"), ("待", "ま"),
            ("立つ", "たつ"), ("立", "た"),
            ("教える", "おしえる"), ("教え", "おしえ"),
            ("考える", "かんがえる"), ("考え", "かんがえ"),
            ("借りる", "かりる"), ("借", "か"),
            ("出る", "でる"), ("出", "で"),
            ("泳ぐ", "およぐ"), ("泳", "およ"),
            ("急ぐ", "いそぐ"), ("急", "いそ"),
            ("信じる", "しんじる"), ("信じ", "しんじ"),
            ("感じる", "かんじる"), ("感じ", "かんじ"),
            ("覚える", "おぼえる"), ("覚え", "おぼえ"),
            ("届ける", "とどける"), ("届け", "とどけ"),
            ("調べる", "しらべる"), ("調べ", "しらべ"),
            ("帰る", "かえる"), ("帰", "かえ"),
            ("変える", "かえる"), ("変え", "かえ"),
            ("聞く", "きく"), ("聞", "き"),
            ("会う", "あう"), ("会", "あ"),
            ("来る", "くる"), ("来", "き"),
        ]
        for k, v in kanji_kana_pairs:
            t = t.replace(k, v)
        # Katakana to Hiragana conversion
        katakana_chars = [chr(i) for i in range(0x30A1, 0x30F7)]
        for kc in katakana_chars:
            hc = chr(ord(kc) - 0x60)
            t = t.replace(kc, hc)
        return t

    def _normalize(self, text: str) -> str:
        """Normalize Japanese text for comparison: strip spaces/punct, hiragana normalize."""
        if not text:
            return ""
        t = text.strip()
        # Remove spaces and Japanese/ASCII punctuation
        t = re.sub(r"[。！？、\s\!\?\,\.\u3000]+", "", t)
        return t

    def explain(self, verb: str, form: ConjugationForm | str) -> str:
        target = self.conjugate(verb, form)
        base = f"{verb} ({target.verb_class.value}) → {target.form.value} = {target.canonical}"
        if target.accepted and len(target.accepted) > 1:
            base += f" (cũng chấp nhận: {', '.join(target.accepted)})"
        if target.variant_notes:
            base += f" — {'; '.join(target.variant_notes)}"
        return base
