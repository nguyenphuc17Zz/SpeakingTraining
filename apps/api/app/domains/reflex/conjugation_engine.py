"""JapaneseConjugationEngine — deterministic conjugation + acceptable variants.

Covers 50 complete forms across:
- Core 12 forms (辞書, ない, た, て, 可能, 受身, 使役, 使役受身, 命令, 意向, ば, たら)
- Group 2: Desire (たい, たくない, たかった, たくなかった, たがる)
- Group 3: Prohibition & Requests (禁止 〜な, ないで, なさい)
- Group 4: State & Prep (ている, ていない, ていた, ておく, てしまう, てみる)
- Group 5: Ease & Difficulty (やすい, にくい, づらい)
- Group 6: Past & Combined (なかった, 受身過去, 使役過去, 使役受身過去, 可能否定, 可能過去, 可能過去否定)
- Group 7: Conditionals (なければ, なかったら, と, なら)
- Group 8: Colloquial Slang (なきゃ, ちゃう, ちゃった, とく, といた, てる, てない, てた, ちゃだめ, ちゃいけない, ないと)

Supports ichidan / godan / irregular (する/来る) + 行く special handling.
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
    # Core (12)
    DICTIONARY = "dictionary"                      # 辞書形
    NAI = "nai"                                    # ない形
    TA = "ta"                                      # た形
    TE = "te"                                      # て形
    POTENTIAL = "potential"                        # 可能形
    PASSIVE = "passive"                            # 受身形
    CAUSATIVE = "causative"                        # 使役形
    CAUSATIVE_PASSIVE = "causative_passive"        # 使役受身形
    IMPERATIVE = "imperative"                      # 命令形
    VOLITIONAL = "volitional"                      # 意向形
    BA = "ba"                                      # ば形
    TARA = "tara"                                  # たら形

    # Group 2: Desire (5)
    TAI = "tai"                                    # たい形
    TAKUNAI = "takunai"                            # たくない形
    TAKATTA = "takatta"                            # たかった形
    TAKUNAKATTA = "takunakatta"                    # たくなかった形
    TAGARU = "tagaru"                              # たがる形

    # Group 3: Prohibition & Requests (3)
    PROHIBITIVE = "prohibitive"                    # 禁止形
    NAIDE = "naide"                                # ないで形
    NASAI = "nasai"                                # なさい形

    # Group 4: State & Prep (6)
    TE_IRU = "te_iru"                              # ている形
    TE_INAI = "te_inai"                            # ていない形
    TE_ITA = "te_ita"                              # ていた形
    TE_OKU = "te_oku"                              # ておく形
    TE_SHIMAU = "te_shimau"                        # てしまう形
    TE_MIRU = "te_miru"                            # てみる形

    # Group 5: Ease & Difficulty (3)
    YASUI = "yasui"                                # やすい形
    NIKUI = "nikui"                                # にくい形
    ZURAI = "zurai"                                # づらい形

    # Group 6: Past & Combined Forms (7)
    NAKATTA = "nakatta"                            # なかった形 (Quá khứ phủ định ngắn)
    PASSIVE_PAST = "passive_past"                  # 受身・過去形
    CAUSATIVE_PAST = "causative_past"              # 使役・過去形
    CAUSATIVE_PASSIVE_PAST = "causative_passive_past" # 使役受身・過去形
    POTENTIAL_NEGATIVE = "potential_negative"      # 可能・否定形
    POTENTIAL_PAST = "potential_past"              # 可能・過去形
    POTENTIAL_NEGATIVE_PAST = "potential_negative_past" # 可能・過去否定形

    # Group 7: Conditionals (4)
    NAKEREBA = "nakereba"                          # なければ形
    NAKATTARA = "nakattara"                        # なかったら形
    TO_CONDITIONAL = "to_conditional"              # と形
    NARA = "nara"                                  # なら形

    # Group 8: Colloquial Slang (11)
    NAKYA = "nakya"                                # 〜なきゃ形
    CHAU = "chau"                                  # 〜ちゃう形
    CHATTA = "chatta"                              # 〜ちゃった形
    TOKU = "toku"                                  # 〜とく形
    TOITA = "toita"                                # 〜といた形
    TERU = "teru"                                  # 〜てる形
    TENAI = "tenai"                                # 〜てない形
    TETA = "teta"                                  # 〜てた形
    CHA_DAME = "cha_dame"                          # 〜ちゃだめ形
    CHA_IKENAI = "cha_ikenai"                      # 〜ちゃいけない形
    NAITO = "naito"                                # 〜ないと形


# Godan ending maps: dict[ending_kana] -> transforms
GODAN_A_MAP = {"う": "わ", "く": "か", "ぐ": "が", "す": "さ", "つ": "た", "ぬ": "な", "ぶ": "ば", "む": "ま", "る": "ら"}
GODAN_I_MAP = {"う": "い", "く": "き", "ぐ": "ぎ", "す": "し", "つ": "ち", "ぬ": "に", "ぶ": "び", "む": "み", "る": "り"}
GODAN_E_MAP = {"う": "え", "く": "け", "ぐ": "げ", "す": "せ", "つ": "て", "ぬ": "ね", "ぶ": "べ", "む": "め", "る": "れ"}
GODAN_O_MAP = {"う": "お", "く": "こ", "ぐ": "ご", "す": "そ", "つ": "と", "ぬ": "の", "ぶ": "ぼ", "む": "も", "る": "ろ"}

# Special 行く past/te forms
IKU_EXCEPTIONS = {"行く", "いく", "イク"}


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
        "食べられる", "たべられる",
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
            if len(v) >= 2:
                pre = v[-2]
                e_row = set("えけげせぜてでねへべぺめれ")
                i_row = set("いきぎしじちぢにひびぴみり")
                if pre in e_row or pre in i_row:
                    if v not in self.KNOWN_GODAN:
                        return VerbClass.ICHIDAN
            return VerbClass.GODAN
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

    def _get_masu_stem(self, verb: str, vc: VerbClass) -> str:
        if vc == VerbClass.ICHIDAN:
            return verb[:-1] if verb.endswith("る") else verb
        if vc == VerbClass.SURU:
            return verb[:-2] + "し" if verb.endswith("する") else "し"
        if vc == VerbClass.KURU:
            is_compound = verb not in ("来る", "くる") and len(verb) > 2
            base = verb[:-2] if is_compound else ""
            return base + ("き" if verb == "くる" else "来")
        return self._godan_stem(verb, "i")

    def _get_nai_stem(self, verb: str, vc: VerbClass) -> str:
        if vc == VerbClass.ICHIDAN:
            return verb[:-1] if verb.endswith("る") else verb
        if vc == VerbClass.SURU:
            return verb[:-2] + "し" if verb.endswith("する") else "し"
        if vc == VerbClass.KURU:
            is_compound = verb not in ("来る", "くる") and len(verb) > 2
            base = verb[:-2] if is_compound else ""
            return base + ("こ" if verb == "くる" else "来")
        return self._godan_stem(verb, "a")

    def _get_te_ta(self, verb: str, vc: VerbClass) -> tuple[str, str]:
        if vc == VerbClass.ICHIDAN:
            stem = verb[:-1] if verb.endswith("る") else verb
            return stem + "て", stem + "た"
        if vc == VerbClass.SURU:
            base = verb[:-2] if verb.endswith("する") else ""
            return base + "して", base + "した"
        if vc == VerbClass.KURU:
            is_compound = verb not in ("来る", "くる") and len(verb) > 2
            base = verb[:-2] if is_compound else ""
            k_te = "きて" if verb == "くる" else "来て"
            k_ta = "きた" if verb == "くる" else "来た"
            return base + k_te, base + k_ta
        return self._godan_te_ta(verb)

    def conjugate(self, verb: str, form: ConjugationForm | str) -> ConjugationTarget:
        if isinstance(form, str):
            form_map = {
                # Core 12
                "辞書形": ConjugationForm.DICTIONARY, "dictionary": ConjugationForm.DICTIONARY,
                "ない形": ConjugationForm.NAI, "ない": ConjugationForm.NAI, "nai": ConjugationForm.NAI,
                "た形": ConjugationForm.TA, "た": ConjugationForm.TA, "ta": ConjugationForm.TA,
                "て形": ConjugationForm.TE, "て": ConjugationForm.TE, "te": ConjugationForm.TE,
                "可能形": ConjugationForm.POTENTIAL, "potential": ConjugationForm.POTENTIAL, "可能": ConjugationForm.POTENTIAL,
                "受身形": ConjugationForm.PASSIVE, "passive": ConjugationForm.PASSIVE, "受身": ConjugationForm.PASSIVE,
                "使役形": ConjugationForm.CAUSATIVE, "causative": ConjugationForm.CAUSATIVE, "使役": ConjugationForm.CAUSATIVE,
                "使役受身形": ConjugationForm.CAUSATIVE_PASSIVE, "causative_passive": ConjugationForm.CAUSATIVE_PASSIVE, "使役受身": ConjugationForm.CAUSATIVE_PASSIVE,
                "命令形": ConjugationForm.IMPERATIVE, "imperative": ConjugationForm.IMPERATIVE, "命令": ConjugationForm.IMPERATIVE,
                "意向形": ConjugationForm.VOLITIONAL, "volitional": ConjugationForm.VOLITIONAL, "意向": ConjugationForm.VOLITIONAL,
                "ば形": ConjugationForm.BA, "ba": ConjugationForm.BA, "ば": ConjugationForm.BA,
                "たら形": ConjugationForm.TARA, "tara": ConjugationForm.TARA, "たら": ConjugationForm.TARA,

                # Group 2: Desire
                "たい形": ConjugationForm.TAI, "たい": ConjugationForm.TAI, "tai": ConjugationForm.TAI,
                "たくない形": ConjugationForm.TAKUNAI, "たくない": ConjugationForm.TAKUNAI, "takunai": ConjugationForm.TAKUNAI,
                "たかった形": ConjugationForm.TAKATTA, "たかった": ConjugationForm.TAKATTA, "takatta": ConjugationForm.TAKATTA,
                "たくなかった形": ConjugationForm.TAKUNAKATTA, "たくなかった": ConjugationForm.TAKUNAKATTA, "takunakatta": ConjugationForm.TAKUNAKATTA,
                "たがる形": ConjugationForm.TAGARU, "たがる": ConjugationForm.TAGARU, "tagaru": ConjugationForm.TAGARU,

                # Group 3: Prohibition & Requests
                "禁止形": ConjugationForm.PROHIBITIVE, "禁止": ConjugationForm.PROHIBITIVE, "prohibitive": ConjugationForm.PROHIBITIVE,
                "ないで形": ConjugationForm.NAIDE, "ないで": ConjugationForm.NAIDE, "naide": ConjugationForm.NAIDE,
                "なさい形": ConjugationForm.NASAI, "なさい": ConjugationForm.NASAI, "nasai": ConjugationForm.NASAI,

                # Group 4: State & Prep
                "ている形": ConjugationForm.TE_IRU, "ている": ConjugationForm.TE_IRU, "te_iru": ConjugationForm.TE_IRU,
                "ていない形": ConjugationForm.TE_INAI, "ていない": ConjugationForm.TE_INAI, "te_inai": ConjugationForm.TE_INAI,
                "ていた形": ConjugationForm.TE_ITA, "ていた": ConjugationForm.TE_ITA, "te_ita": ConjugationForm.TE_ITA,
                "ておく形": ConjugationForm.TE_OKU, "ておく": ConjugationForm.TE_OKU, "te_oku": ConjugationForm.TE_OKU,
                "てしまう形": ConjugationForm.TE_SHIMAU, "てしまう": ConjugationForm.TE_SHIMAU, "te_shimau": ConjugationForm.TE_SHIMAU,
                "てみる形": ConjugationForm.TE_MIRU, "てみる": ConjugationForm.TE_MIRU, "te_miru": ConjugationForm.TE_MIRU,

                # Group 5: Ease & Difficulty
                "やすい形": ConjugationForm.YASUI, "やすい": ConjugationForm.YASUI, "yasui": ConjugationForm.YASUI,
                "にくい形": ConjugationForm.NIKUI, "にくい": ConjugationForm.NIKUI, "nikui": ConjugationForm.NIKUI,
                "づらい形": ConjugationForm.ZURAI, "づらい": ConjugationForm.ZURAI, "zurai": ConjugationForm.ZURAI,

                # Group 6: Past & Combined
                "なかった形": ConjugationForm.NAKATTA, "なかった": ConjugationForm.NAKATTA, "nakatta": ConjugationForm.NAKATTA,
                "受身・過去形": ConjugationForm.PASSIVE_PAST, "受身過去": ConjugationForm.PASSIVE_PAST, "受身・過去": ConjugationForm.PASSIVE_PAST, "passive_past": ConjugationForm.PASSIVE_PAST,
                "使役・過去形": ConjugationForm.CAUSATIVE_PAST, "使役過去": ConjugationForm.CAUSATIVE_PAST, "使役・過去": ConjugationForm.CAUSATIVE_PAST, "causative_past": ConjugationForm.CAUSATIVE_PAST,
                "使役受身・過去形": ConjugationForm.CAUSATIVE_PASSIVE_PAST, "使役受身過去": ConjugationForm.CAUSATIVE_PASSIVE_PAST, "使役受身・過去": ConjugationForm.CAUSATIVE_PASSIVE_PAST, "causative_passive_past": ConjugationForm.CAUSATIVE_PASSIVE_PAST,
                "可能・否定形": ConjugationForm.POTENTIAL_NEGATIVE, "可能否定": ConjugationForm.POTENTIAL_NEGATIVE, "可能・否定": ConjugationForm.POTENTIAL_NEGATIVE, "potential_negative": ConjugationForm.POTENTIAL_NEGATIVE,
                "可能・過去形": ConjugationForm.POTENTIAL_PAST, "可能過去": ConjugationForm.POTENTIAL_PAST, "可能・過去": ConjugationForm.POTENTIAL_PAST, "potential_past": ConjugationForm.POTENTIAL_PAST,
                "可能・過去否定形": ConjugationForm.POTENTIAL_NEGATIVE_PAST, "可能過去否定": ConjugationForm.POTENTIAL_NEGATIVE_PAST, "可能・過去否定": ConjugationForm.POTENTIAL_NEGATIVE_PAST, "potential_negative_past": ConjugationForm.POTENTIAL_NEGATIVE_PAST,

                # Group 7: Conditionals
                "なければ形": ConjugationForm.NAKEREBA, "なければ": ConjugationForm.NAKEREBA, "nakereba": ConjugationForm.NAKEREBA,
                "なかったら形": ConjugationForm.NAKATTARA, "なかったら": ConjugationForm.NAKATTARA, "nakattara": ConjugationForm.NAKATTARA,
                "と形": ConjugationForm.TO_CONDITIONAL, "と": ConjugationForm.TO_CONDITIONAL, "to_conditional": ConjugationForm.TO_CONDITIONAL,
                "なら形": ConjugationForm.NARA, "なら": ConjugationForm.NARA, "nara": ConjugationForm.NARA,

                # Group 8: Colloquial Slang
                "なきゃ形": ConjugationForm.NAKYA, "なきゃ": ConjugationForm.NAKYA, "nakya": ConjugationForm.NAKYA,
                "ちゃう形": ConjugationForm.CHAU, "ちゃう": ConjugationForm.CHAU, "chau": ConjugationForm.CHAU,
                "ちゃった形": ConjugationForm.CHATTA, "ちゃった": ConjugationForm.CHATTA, "chatta": ConjugationForm.CHATTA,
                "とく形": ConjugationForm.TOKU, "とく": ConjugationForm.TOKU, "toku": ConjugationForm.TOKU,
                "といた形": ConjugationForm.TOITA, "といた": ConjugationForm.TOITA, "toita": ConjugationForm.TOITA,
                "てる形": ConjugationForm.TERU, "てる": ConjugationForm.TERU, "teru": ConjugationForm.TERU,
                "てない形": ConjugationForm.TENAI, "てない": ConjugationForm.TENAI, "tenai": ConjugationForm.TENAI,
                "てた形": ConjugationForm.TETA, "てた": ConjugationForm.TETA, "teta": ConjugationForm.TETA,
                "ちゃだめ形": ConjugationForm.CHA_DAME, "ちゃだめ": ConjugationForm.CHA_DAME, "cha_dame": ConjugationForm.CHA_DAME,
                "ちゃいけない形": ConjugationForm.CHA_IKENAI, "ちゃいけない": ConjugationForm.CHA_IKENAI, "cha_ikenai": ConjugationForm.CHA_IKENAI,
                "ないと形": ConjugationForm.NAITO, "ないと": ConjugationForm.NAITO, "naito": ConjugationForm.NAITO,
            }
            form = form_map.get(form, ConjugationForm.DICTIONARY)

        vc = self.identify_verb_class(verb)
        canonical, accepted, alternatives, notes = self._generate(verb, vc, form)
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

        # Base stems
        masu_stem = self._get_masu_stem(verb, vc)
        nai_stem = self._get_nai_stem(verb, vc)
        te_form, ta_form = self._get_te_ta(verb, vc)

        # Helper for Te-based colloquial endings
        te_is_de = te_form.endswith("で")
        te_stem = te_form[:-1]

        # ==========================================
        # GROUP 2: DESIRE (HỆ TAI)
        # ==========================================
        if form == ConjugationForm.TAI:
            return masu_stem + "たい", [], [], []
        if form == ConjugationForm.TAKUNAI:
            return masu_stem + "たくない", [], [], []
        if form == ConjugationForm.TAKATTA:
            return masu_stem + "たかった", [], [], []
        if form == ConjugationForm.TAKUNAKATTA:
            return masu_stem + "たくなかった", [], [], []
        if form == ConjugationForm.TAGARU:
            return masu_stem + "たがる", [], [], []

        # ==========================================
        # GROUP 3: PROHIBITION & REQUESTS
        # ==========================================
        if form == ConjugationForm.PROHIBITIVE:
            return verb + "な", [], [], ["禁止形 = V-る + な"]
        if form == ConjugationForm.NAIDE:
            canon = nai_stem + "ないで"
            return canon, [canon, canon + "ください"], [], []
        if form == ConjugationForm.NASAI:
            return masu_stem + "なさい", [], [], []

        # ==========================================
        # GROUP 4: STATE & PREPARATION (HỆ TE)
        # ==========================================
        if form == ConjugationForm.TE_IRU:
            canon = te_form + "いる"
            coll = te_stem + ("でる" if te_is_de else "てる")
            return canon, [canon, coll], [coll], ["V-ている rút gọn thành 〜てる"]
        if form == ConjugationForm.TE_INAI:
            canon = te_form + "いない"
            coll = te_stem + ("でない" if te_is_de else "てない")
            return canon, [canon, coll], [coll], ["V-ていない rút gọn thành 〜てない"]
        if form == ConjugationForm.TE_ITA:
            canon = te_form + "いた"
            coll = te_stem + ("でた" if te_is_de else "てた")
            return canon, [canon, coll], [coll], ["V-ていた rút gọn thành 〜てた"]
        if form == ConjugationForm.TE_OKU:
            canon = te_form + "おく"
            coll = te_stem + ("どく" if te_is_de else "とく")
            return canon, [canon, coll], [coll], ["V-ておく rút gọn thành 〜とく"]
        if form == ConjugationForm.TE_SHIMAU:
            canon = te_form + "しまう"
            coll = te_stem + ("じゃう" if te_is_de else "ちゃう")
            return canon, [canon, coll], [coll], ["V-てしまう rút gọn thành 〜ちゃう"]
        if form == ConjugationForm.TE_MIRU:
            return te_form + "みる", [], [], []

        # ==========================================
        # GROUP 5: EASE & DIFFICULTY
        # ==========================================
        if form == ConjugationForm.YASUI:
            return masu_stem + "やすい", [], [], []
        if form == ConjugationForm.NIKUI:
            return masu_stem + "にくい", [], [], []
        if form == ConjugationForm.ZURAI:
            return masu_stem + "づらい", [], [], []

        # ==========================================
        # GROUP 6: PAST & COMBINED FORMS
        # ==========================================
        if form == ConjugationForm.NAKATTA:
            return nai_stem + "なかった", [], [], []

        # ==========================================
        # GROUP 7: CONDITIONALS
        # ==========================================
        if form == ConjugationForm.NAKEREBA:
            canon = nai_stem + "なければ"
            coll = nai_stem + "なきゃ"
            coll2 = nai_stem + "なくちゃ"
            return canon, [canon, coll, coll2], [coll], ["〜なければ rút gọn thành 〜なきゃ"]
        if form == ConjugationForm.NAKATTARA:
            return nai_stem + "なかったら", [], [], []
        if form == ConjugationForm.TO_CONDITIONAL:
            return verb + "と", [], [], []
        if form == ConjugationForm.NARA:
            return verb + "なら", [], [], []

        # ==========================================
        # GROUP 8: COLLOQUIAL SLANG
        # ==========================================
        if form == ConjugationForm.NAKYA:
            canon = nai_stem + "なきゃ"
            return canon, [canon, nai_stem + "なくちゃ", nai_stem + "なければ"], [], ["Phải làm = 〜なきゃ / 〜なくちゃ"]
        if form == ConjugationForm.CHAU:
            canon = te_stem + ("じゃう" if te_is_de else "ちゃう")
            return canon, [canon, te_form + "しまう"], [], ["Lỡ làm = 〜ちゃう"]
        if form == ConjugationForm.CHATTA:
            canon = te_stem + ("じゃった" if te_is_de else "ちゃった")
            return canon, [canon, te_form + "しまった"], [], ["Đã lỡ làm = 〜ちゃった"]
        if form == ConjugationForm.TOKU:
            canon = te_stem + ("どく" if te_is_de else "とく")
            return canon, [canon, te_form + "おく"], [], ["Làm sẵn = 〜とく"]
        if form == ConjugationForm.TOITA:
            canon = te_stem + ("どいた" if te_is_de else "といた")
            return canon, [canon, te_form + "おいた"], [], ["Đã làm sẵn = 〜といた"]
        if form == ConjugationForm.TERU:
            canon = te_stem + ("でる" if te_is_de else "てる")
            return canon, [canon, te_form + "いる"], [], ["Đang làm = 〜てる"]
        if form == ConjugationForm.TENAI:
            canon = te_stem + ("でない" if te_is_de else "てない")
            return canon, [canon, te_form + "いない"], [], ["Chưa làm = 〜てない"]
        if form == ConjugationForm.TETA:
            canon = te_stem + ("でた" if te_is_de else "てた")
            return canon, [canon, te_form + "いた"], [], ["Đã đang làm = 〜てた"]
        if form == ConjugationForm.CHA_DAME:
            canon = te_stem + ("じゃだめ" if te_is_de else "ちゃだめ")
            return canon, [canon, te_form + "はだめ", te_stem + ("じゃダメ" if te_is_de else "ちゃダメ")], [], ["Không được làm = 〜ちゃだめ"]
        if form == ConjugationForm.CHA_IKENAI:
            canon = te_stem + ("じゃいけない" if te_is_de else "ちゃいけない")
            return canon, [canon, te_form + "はいけない", te_stem + ("じゃダメ" if te_is_de else "ちゃダメ")], [], ["Không được làm = 〜ちゃいけない"]
        if form == ConjugationForm.NAITO:
            canon = nai_stem + "ないと"
            return canon, [canon, nai_stem + "ないといけない", nai_stem + "ないとだめ"], [], ["Phải làm = 〜ないと"]

        # ==========================================
        # SURU CLASS HANDLING
        # ==========================================
        if vc == VerbClass.SURU:
            base = verb[:-2] if verb.endswith("する") else ""
            mapping = {
                ConjugationForm.NAI: "しない",
                ConjugationForm.TA: "した",
                ConjugationForm.TE: "して",
                ConjugationForm.POTENTIAL: "できる",
                ConjugationForm.POTENTIAL_NEGATIVE: "できない",
                ConjugationForm.POTENTIAL_PAST: "できた",
                ConjugationForm.POTENTIAL_NEGATIVE_PAST: "できなかった",
                ConjugationForm.PASSIVE: "される",
                ConjugationForm.PASSIVE_PAST: "された",
                ConjugationForm.CAUSATIVE: "させる",
                ConjugationForm.CAUSATIVE_PAST: "させた",
                ConjugationForm.CAUSATIVE_PASSIVE: "させられる",
                ConjugationForm.CAUSATIVE_PASSIVE_PAST: "させられた",
                ConjugationForm.IMPERATIVE: "しろ",
                ConjugationForm.VOLITIONAL: "しよう",
                ConjugationForm.BA: "すれば",
                ConjugationForm.TARA: "したら",
            }
            canon = base + mapping.get(form, verb)
            if form == ConjugationForm.CAUSATIVE_PASSIVE:
                accepted = [canon, base + "される"] if base else [canon]
                notes.append("使役受身 của する có thể rút gọn")
            elif form == ConjugationForm.IMPERATIVE:
                alternatives = [base + "せよ"] if base else []
            return canon, accepted, alternatives, notes

        # ==========================================
        # KURU CLASS HANDLING
        # ==========================================
        if vc == VerbClass.KURU:
            is_compound = verb not in ("来る", "くる") and len(verb) > 2
            base = verb[:-2] if is_compound else ""
            is_hira = verb == "くる"

            if is_hira:
                mapping = {
                    ConjugationForm.NAI: "こない",
                    ConjugationForm.TA: "きた",
                    ConjugationForm.TE: "きて",
                    ConjugationForm.POTENTIAL: "こられる",
                    ConjugationForm.POTENTIAL_NEGATIVE: "こられない",
                    ConjugationForm.POTENTIAL_PAST: "こられた",
                    ConjugationForm.POTENTIAL_NEGATIVE_PAST: "こられなかった",
                    ConjugationForm.PASSIVE: "こられる",
                    ConjugationForm.PASSIVE_PAST: "こられた",
                    ConjugationForm.CAUSATIVE: "こさせる",
                    ConjugationForm.CAUSATIVE_PAST: "こさせた",
                    ConjugationForm.CAUSATIVE_PASSIVE: "こさせられる",
                    ConjugationForm.CAUSATIVE_PASSIVE_PAST: "こさせられた",
                    ConjugationForm.IMPERATIVE: "こい",
                    ConjugationForm.VOLITIONAL: "こよう",
                    ConjugationForm.BA: "くれば",
                    ConjugationForm.TARA: "きたら",
                }
            else:
                mapping = {
                    ConjugationForm.NAI: base + "来ない",
                    ConjugationForm.TA: base + "来た",
                    ConjugationForm.TE: base + "来て",
                    ConjugationForm.POTENTIAL: base + "来られる",
                    ConjugationForm.POTENTIAL_NEGATIVE: base + "来られない",
                    ConjugationForm.POTENTIAL_PAST: base + "来られた",
                    ConjugationForm.POTENTIAL_NEGATIVE_PAST: base + "来られなかった",
                    ConjugationForm.PASSIVE: base + "来られる",
                    ConjugationForm.PASSIVE_PAST: base + "来られた",
                    ConjugationForm.CAUSATIVE: base + "来させる",
                    ConjugationForm.CAUSATIVE_PAST: base + "来させた",
                    ConjugationForm.CAUSATIVE_PASSIVE: base + "来させられる",
                    ConjugationForm.CAUSATIVE_PASSIVE_PAST: base + "来させられた",
                    ConjugationForm.IMPERATIVE: base + "来い",
                    ConjugationForm.VOLITIONAL: base + "来よう",
                    ConjugationForm.BA: base + "来れば",
                    ConjugationForm.TARA: base + "来たら",
                }
            canon = mapping.get(form, verb)
            if form == ConjugationForm.POTENTIAL:
                accepted = [canon, base + ("これる" if is_hira else "来れる")]
            elif form == ConjugationForm.POTENTIAL_NEGATIVE:
                accepted = [canon, base + ("これない" if is_hira else "来れない")]
            elif form == ConjugationForm.POTENTIAL_PAST:
                accepted = [canon, base + ("これた" if is_hira else "来れた")]
            elif form == ConjugationForm.POTENTIAL_NEGATIVE_PAST:
                accepted = [canon, base + ("これなかった" if is_hira else "来れなかった")]
            return canon, accepted, alternatives, notes

        # ==========================================
        # ICHIDAN CLASS HANDLING
        # ==========================================
        if vc == VerbClass.ICHIDAN:
            stem = verb[:-1] if verb.endswith("る") else verb
            mapping = {
                ConjugationForm.NAI: stem + "ない",
                ConjugationForm.TA: stem + "た",
                ConjugationForm.TE: stem + "て",
                ConjugationForm.POTENTIAL: stem + "られる",
                ConjugationForm.POTENTIAL_NEGATIVE: stem + "られない",
                ConjugationForm.POTENTIAL_PAST: stem + "られた",
                ConjugationForm.POTENTIAL_NEGATIVE_PAST: stem + "られなかった",
                ConjugationForm.PASSIVE: stem + "られる",
                ConjugationForm.PASSIVE_PAST: stem + "られた",
                ConjugationForm.CAUSATIVE: stem + "させる",
                ConjugationForm.CAUSATIVE_PAST: stem + "させた",
                ConjugationForm.CAUSATIVE_PASSIVE: stem + "させられる",
                ConjugationForm.CAUSATIVE_PASSIVE_PAST: stem + "させられた",
                ConjugationForm.IMPERATIVE: stem + "ろ",
                ConjugationForm.VOLITIONAL: stem + "よう",
                ConjugationForm.BA: stem + "れば",
                ConjugationForm.TARA: stem + "たら",
            }
            canon = mapping.get(form, verb)
            if form == ConjugationForm.POTENTIAL:
                accepted = [canon, stem + "れる"]
            elif form == ConjugationForm.POTENTIAL_NEGATIVE:
                accepted = [canon, stem + "れない"]
            elif form == ConjugationForm.POTENTIAL_PAST:
                accepted = [canon, stem + "れた"]
            elif form == ConjugationForm.POTENTIAL_NEGATIVE_PAST:
                accepted = [canon, stem + "れなかった"]
            elif form == ConjugationForm.IMPERATIVE:
                accepted = [canon, stem + "よ"]
            return canon, accepted, alternatives, notes

        # ==========================================
        # GODAN CLASS HANDLING
        # ==========================================
        if form == ConjugationForm.NAI:
            return self._godan_stem(verb, "a") + "ない", [], [], []
        if form == ConjugationForm.TA:
            return ta_form, [], [], []
        if form == ConjugationForm.TE:
            return te_form, [], [], []
        if form == ConjugationForm.POTENTIAL:
            canon = self._godan_stem(verb, "e") + "る"
            return canon, [], [], []
        if form == ConjugationForm.POTENTIAL_NEGATIVE:
            canon = self._godan_stem(verb, "e") + "ない"
            return canon, [], [], []
        if form == ConjugationForm.POTENTIAL_PAST:
            canon = self._godan_stem(verb, "e") + "た"
            return canon, [], [], []
        if form == ConjugationForm.POTENTIAL_NEGATIVE_PAST:
            canon = self._godan_stem(verb, "e") + "なかった"
            return canon, [], [], []
        if form == ConjugationForm.PASSIVE:
            canon = self._godan_stem(verb, "a") + "れる"
            return canon, [], [], []
        if form == ConjugationForm.PASSIVE_PAST:
            canon = self._godan_stem(verb, "a") + "れた"
            return canon, [], [], []
        if form == ConjugationForm.CAUSATIVE:
            canon = self._godan_stem(verb, "a") + "せる"
            return canon, [], [], []
        if form == ConjugationForm.CAUSATIVE_PAST:
            canon = self._godan_stem(verb, "a") + "せた"
            return canon, [], [], []
        if form == ConjugationForm.CAUSATIVE_PASSIVE:
            canon = self._godan_stem(verb, "a") + "せられる"
            contracted = self._godan_stem(verb, "a") + "される"
            return canon, [canon, contracted], [contracted], ["使役受身 godan chấp nhận cả せられる và される"]
        if form == ConjugationForm.CAUSATIVE_PASSIVE_PAST:
            canon = self._godan_stem(verb, "a") + "せられた"
            contracted = self._godan_stem(verb, "a") + "された"
            return canon, [canon, contracted], [contracted], ["使役受身過去 godan chấp nhận cả せられた và された"]
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
            if ta_form.endswith("た"):
                canon = ta_form[:-1] + "たら"
            elif ta_form.endswith("だ"):
                canon = ta_form[:-1] + "だら"
            else:
                canon = ta_form + "ら"
            return canon, [], [], []

        return verb, [], [], []

    def validate(self, verb: str, form: ConjugationForm | str, answer: str, normalize: bool = True) -> dict[str, Any]:
        """Validates user answer against expected conjugation."""
        target = self.conjugate(verb, form)
        ans_norm = self._normalize(answer) if normalize else answer.strip()
        ans_kana = self._to_kana(ans_norm)

        accepted_norm = [self._normalize(a) for a in target.accepted]
        accepted_kana = [self._to_kana(a) for a in accepted_norm]

        is_match = (
            ans_norm == self._normalize(target.canonical)
            or ans_norm in accepted_norm
            or ans_kana == self._to_kana(self._normalize(target.canonical))
            or ans_kana in accepted_kana
        )

        return {
            "is_correct": is_match,
            "canonical": target.canonical,
            "accepted": target.accepted,
            "matched_form": target.form.value,
            "variant_notes": target.variant_notes,
            "reading": target.reading,
        }

    def _normalize(self, text: str) -> str:
        t = text.strip()
        t = re.sub(r"[\s\u3000、。！？!?]+", "", t)
        return t

    def _to_kana(self, text: str) -> str:
        # Normalize katakana to hiragana
        result = []
        for ch in text:
            code = ord(ch)
            if 0x30A1 <= code <= 0x30F6:
                result.append(chr(code - 0x60))
            else:
                result.append(ch)
        return "".join(result)
