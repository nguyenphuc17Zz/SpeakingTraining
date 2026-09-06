import pytest

from app.domains.situations.intent_resolver import IntentResolver


def test_intent_resolver_direct_and_semantic():
    resolver = IntentResolver()

    # 1. Direct regex match
    res1 = resolver.resolve("ビールを一つください")
    assert res1["intent"] == "ORDER_DRINK"
    assert res1["confidence"] >= 0.90
    assert any(e["value"] == "ビール" for e in res1["entities"])

    # 2. Semantic prototype match (not in legacy regex table, e.g. "アイスコーヒーをいただけますか")
    res2 = resolver.resolve("アイスコーヒーをいただけますか")
    assert res2["intent"] == "ORDER_DRINK"
    assert res2["confidence"] >= 0.75

    # 3. Food order with different word: "カレーを頼みます"
    res3 = resolver.resolve("カレーを頼みます")
    assert res3["intent"] == "ORDER_FOOD"
    assert res3["confidence"] >= 0.75

    # 4. Decline bag
    res4 = resolver.resolve("レジ袋はいりません、大丈夫です")
    assert res4["intent"] == "DECLINE_BAG"

    # 5. Dialogue acts
    assert resolver._dialogue_act("トイレはどこですか？") == "QUESTION"
    assert resolver._dialogue_act("ありがとうございます！") == "THANK"
