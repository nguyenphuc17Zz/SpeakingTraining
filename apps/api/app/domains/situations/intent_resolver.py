"""IntentResolver + EntityExtractor + DialogueAct — generic, not scenario-specific parsers."""

from __future__ import annotations

import re
from typing import Any


# Generic intent keywords (small, not giant) — ORDER_FOOD now product-specific to avoid generic REQUEST overlap
INTENT_KEYWORDS = {
    "DECLINE_BAG": [r"袋.*いりません", r"袋.*結構です", r"袋.*いらない"],
    "ORDER_FOOD": [r"おにぎり.*ください", r"枝豆.*ください", r"焼き鳥.*ください", r"ラーメン.*ください", r"注文.*ください", r"おにぎり.*お願い"],
    "ORDER_DRINK": [r"ビール.*ください", r"ビール.*お願い", r"飲み物.*ください", r"生.*ください", r"生.*お願い"],
    "ASK_RECOMMENDATION": [r"おすすめ", r"お勧め"],
    "REQUEST": [r"お願いします", r"お願い", r"ください", r"していただけますか"],
    "DECLINE": [r"結構です", r"いりません", r"いらない", r"大丈夫です"],
    "ACCEPT": [r"お願いします", r"はい", r"ください"],
    "CONFIRM": [r"確認", r"で合っていますか"],
    "APOLOGIZE": [r"すみません", r"申し訳"],
    "THANK": [r"ありがとう"],
    "COMPLAIN": [r"間違", r"違う"],
    "BACKCHANNEL": [r"^(はい|うん|なるほど|そうですね|そうなんですね)[。！]?$"],
}

ENTITY_PATTERNS = {
    "product": [r"ビール", r"おにぎり", r"枝豆", r"焼き鳥"],
    "quantity": [r"一つ", r"二つ", r"1つ", r"2つ"],
    "payment_method": [r"現金", r"カード", r"PayPay"],
    "allergy": [r"エビ", r"アレルギー", r"食べられません"],
    "time": [r"\d+時", r"\d+分"],
    "price": [r"\d+円"],
}

DIALOGUE_ACT_KEYWORDS = {
    "REQUEST": [r"ください", r"お願い"],
    "QUESTION": [r"か\？?", r"ですか", r"ますか"],
    "ANSWER": [r"はい", r"そうです"],
    "CONFIRM": [r"確認", r"合っていますか"],
    "DENY": [r"いいえ", r"違います"],
    "ACCEPT": [r"お願いします", r"はい"],
    "DECLINE": [r"結構です", r"いりません"],
    "CLARIFY": [r"もう一度", r"すみません.*聞き"],
    "APOLOGIZE": [r"すみません", r"申し訳"],
    "THANK": [r"ありがとう"],
    "BACKCHANNEL": [r"^(はい|うん|なるほど)"],
}


class IntentResolver:
    def resolve(self, transcript: str) -> dict[str, Any]:
        text = transcript.strip()
        # Check backchannel first (short)
        for intent, patterns in INTENT_KEYWORDS.items():
            for pat in patterns:
                if re.search(pat, text):
                    # Confidence based on match length
                    return {"intent": intent, "entities": self.extract_entities(text), "confidence": 0.92, "dialogue_act": self._dialogue_act(text)}
        # Fallback: unknown but try AI later
        return {"intent": "UNKNOWN", "entities": self.extract_entities(text), "confidence": 0.35, "dialogue_act": self._dialogue_act(text)}

    def extract_entities(self, text: str) -> list[dict[str, Any]]:
        entities = []
        for etype, patterns in ENTITY_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, text):
                    entities.append({"type": etype, "value": re.search(pat, text).group(0) if re.search(pat, text) else "", "source": "regex"})
        return entities

    def _dialogue_act(self, text: str) -> str:
        for act, patterns in DIALOGUE_ACT_KEYWORDS.items():
            for pat in patterns:
                if re.search(pat, text):
                    return act
        return "STATEMENT"


class DialogueActResolver:
    def resolve(self, text: str) -> str:
        return IntentResolver()._dialogue_act(text)
