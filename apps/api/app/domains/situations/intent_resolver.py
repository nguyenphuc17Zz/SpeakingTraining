"""
IntentResolver + EntityExtractor + DialogueAct — Hybrid Regex & Semantic Prototype Classifier.
"""

from __future__ import annotations

import re
from typing import Any

# Fast direct intent regex patterns
INTENT_KEYWORDS: dict[str, list[str]] = {
    "DECLINE_BAG": [r"袋.*(いりません|結構|いらない|大丈夫)", r"レジ袋.*(不要|なし)"],
    "ORDER_FOOD": [
        r"(おにぎり|枝豆|焼き鳥|ラーメン|カレー|定食|パスタ|から揚げ|サンドイッチ|ピザ|料理).*(ください|お願い|頼みます|ちょうだい)",
        r"注文.*(お願い|いいですか|頼み)",
    ],
    "ORDER_DRINK": [
        r"(ビール|生|お茶|水|コーヒー|お冷|コーラ|ウーロン茶|ジュース|お酒|ワイン|ドリンク).*(ください|お願い|頼みます|一杯)",
        r"飲み物.*(頼み|注文|お願い)",
    ],
    "ASK_RECOMMENDATION": [r"おすすめ", r"お勧め", r"一番人気", r"何が人気", r"どれが美味しい", r"名物"],
    "REQUEST": [r"お願いします", r"お願い", r"ください", r"していただけますか", r"頼めますか"],
    "DECLINE": [r"結構です", r"いりません", r"いらない", r"大丈夫です", r"結構だ"],
    "ACCEPT": [r"お願いします", r"はい", r"大丈夫です", r"喜んで", r"了解"],
    "CONFIRM": [r"確認", r"合っていますか", r"間違いない", r"大丈夫ですか"],
    "APOLOGIZE": [r"すみません", r"申し訳", r"失礼しました", r"ごめんなさい"],
    "THANK": [r"ありがとう", r"ごちそうさま", r"どうも"],
    "COMPLAIN": [r"間違", r"違う", r"遅い", r"まだ来ない"],
    "BACKCHANNEL": [r"^(はい|うん|なるほど|そうですね|そうなんですね)[。！]?$"],
}

# Semantic Prototype Clusters for BM25 / dense keyword matching
SEMANTIC_INTENT_PROTOTYPES: dict[str, dict[str, list[str]]] = {
    "ORDER_FOOD": {
        "targets": ["おにぎり", "弁当", "定食", "ラーメン", "カレー", "パスタ", "唐揚げ", "枝豆", "焼き鳥", "料理", "注文", "サンドイッチ", "ご飯", "ピザ", "パン", "サラダ"],
        "triggers": ["ください", "お願いします", "お願い", "頼む", "頼みます", "いただけますか", "一つ", "二つ", "1つ", "2つ", "ちょうだい"],
    },
    "ORDER_DRINK": {
        "targets": ["ビール", "お茶", "水", "コーヒー", "ジュース", "飲み物", "生", "ドリンク", "ハイボール", "ワイン", "ウーロン茶", "お冷", "コーラ", "アイスコーヒー"],
        "triggers": ["ください", "お願いします", "お願い", "頼む", "頼みます", "いただけますか", "一杯", "グラス", "ボトル"],
    },
    "DECLINE_BAG": {
        "targets": ["袋", "レジ袋", "ふくろ", "紙袋"],
        "triggers": ["いりません", "結構", "いらない", "大丈夫", "持参", "マイバッグ", "不要", "結構です"],
    },
    "ASK_RECOMMENDATION": {
        "targets": ["おすすめ", "お勧め", "人気", "一番", "何がいい", "イチオシ", "名物", "看板メニュー", "どれが美味しい"],
        "triggers": ["何", "どれ", "教えて", "ありますか", "ですか"],
    },
    "APOLOGIZE": {
        "targets": ["すみません", "申し訳ありません", "ごめんなさい", "失礼いたします", "恐れ入ります"],
        "triggers": [],
    },
    "THANK": {
        "targets": ["ありがとうございます", "ありがとう", "ごちそうさまでした", "どうも", "感謝いたします"],
        "triggers": [],
    },
}

ENTITY_PATTERNS = {
    "product": [r"(生ビール|ビール|おにぎり|枝豆|焼き鳥|ラーメン|カレー|コーヒー|お茶|定食|パスタ)"],
    "quantity": [r"(一つ|二つ|三つ|四つ|1つ|2つ|3つ|4つ|\d+個|\d+杯|\d+本)"],
    "payment_method": [r"(現金|カード|クレジットカード|PayPay|電子マネー|交通系|Suica|Pasmo)"],
    "allergy": [r"(エビ|カニ|ピーナッツ|小麦|卵|そば|牛乳|アレルギー)"],
    "time": [r"\d+時(\d+分)?"],
    "price": [r"\d+円"],
}

DIALOGUE_ACT_KEYWORDS = {
    "REQUEST": [r"ください", r"お願い", r"いただけますか", r"頼み"],
    "QUESTION": [r"か[\？\?]?$", r"ですか", r"ますか", r"でしょうか"],
    "ANSWER": [r"^はい", r"^そうです", r"^そうですね"],
    "CONFIRM": [r"確認", r"合っていますか", r"ですかね"],
    "DENY": [r"^いいえ", r"違います", r"違くない"],
    "ACCEPT": [r"お願いします", r"^はい", r"了解"],
    "DECLINE": [r"結構です", r"いりません", r"大丈夫です"],
    "CLARIFY": [r"もう一度", r"すみません.*聞き", r"どういうこと"],
    "APOLOGIZE": [r"すみません", r"申し訳"],
    "THANK": [r"ありがとう", r"ごちそうさま"],
    "BACKCHANNEL": [r"^(はい|うん|なるほど|そうですね)"],
}


class IntentResolver:
    """Hybrid fast-path regex and semantic prototype intent resolver."""

    def resolve(self, transcript: str) -> dict[str, Any]:
        text = transcript.strip()
        if not text:
            return {"intent": "UNKNOWN", "entities": [], "confidence": 0.0, "dialogue_act": "STATEMENT"}

        # 1. Direct Regex Match (High Confidence)
        for intent, patterns in INTENT_KEYWORDS.items():
            for pat in patterns:
                if re.search(pat, text):
                    return {
                        "intent": intent,
                        "entities": self.extract_entities(text),
                        "confidence": 0.95,
                        "dialogue_act": self._dialogue_act(text),
                    }

        # 2. Semantic Prototype Overlap (BM25-style hybrid)
        best_intent = None
        best_score = 0.0

        for intent, proto in SEMANTIC_INTENT_PROTOTYPES.items():
            targets = proto["targets"]
            triggers = proto["triggers"]

            target_hits = sum(1 for t in targets if t in text)
            trigger_hits = sum(1 for tr in triggers if tr in text) if triggers else 1

            if target_hits > 0 and trigger_hits > 0:
                score = 0.60 + min(0.30, target_hits * 0.15 + trigger_hits * 0.10)
                if score > best_score:
                    best_score = score
                    best_intent = intent

        if best_intent and best_score >= 0.70:
            return {
                "intent": best_intent,
                "entities": self.extract_entities(text),
                "confidence": round(best_score, 2),
                "dialogue_act": self._dialogue_act(text),
            }

        # 3. Fallback: unknown intent
        return {
            "intent": "UNKNOWN",
            "entities": self.extract_entities(text),
            "confidence": 0.35,
            "dialogue_act": self._dialogue_act(text),
        }

    def extract_entities(self, text: str) -> list[dict[str, Any]]:
        entities: list[dict[str, Any]] = []
        for etype, patterns in ENTITY_PATTERNS.items():
            for pat in patterns:
                m = re.search(pat, text)
                if m:
                    entities.append({
                        "type": etype,
                        "value": m.group(0),
                        "source": "hybrid_regex",
                    })
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
