import pytest
from app.domains.conversation.context import ContextBudgetManager
from app.domains.conversation.models import ConversationTurn


def test_textrank_turn_salience_ranking():
    """Verify that turns with central thematic overlap receive higher TextRank scores."""
    turns = [
        ConversationTurn(sequence=1, speaker="user", transcript="東京の天気を教えてください。"),
        ConversationTurn(sequence=2, speaker="assistant", transcript="東京は今日晴れていて、とても良い天気ですよ。"),
        ConversationTurn(sequence=3, speaker="user", transcript="東京で散歩するのにいい天気ですね。公園はどこがいいですか？"),
        ConversationTurn(sequence=4, speaker="assistant", transcript="上野公園や代々木公園がおすすめですよ。"),
        ConversationTurn(sequence=5, speaker="user", transcript="全く関係ないラーメンの話ですが。"),  # Low overlap
    ]

    salience = ContextBudgetManager.compute_turn_salience(turns)
    assert len(salience) == 5

    # Turn 2 and 3 share core vocabulary (東京, 天気, 公園) with turns 1, 2, 4
    # The unrelated turn (5) should have significantly lower salience
    assert salience[1] > salience[4]
    assert salience[2] > salience[4]


def test_select_budgeted_turns_preserve_premise():
    """Verify premise preservation keeps first 2 turns, last 3 turns, and salient middle turns."""
    turns = [
        ConversationTurn(sequence=0, speaker="user", transcript="Premise turn 1: 私の名前はケンです。日本に留学したいです。"),
        ConversationTurn(sequence=1, speaker="assistant", transcript="Premise turn 2: ケンさん、ようこそ！日本語の練習をしましょう。"),
        # Middle turns
        ConversationTurn(sequence=2, speaker="user", transcript="留学についての質問です。大学選びはどうすればいい？"),
        ConversationTurn(sequence=3, speaker="assistant", transcript="大学選びは専攻と立地が大事ですね。"),
        ConversationTurn(sequence=4, speaker="user", transcript="ふむふむ。"),  # Very low salience / filler
        ConversationTurn(sequence=5, speaker="assistant", transcript="他に気になる点はありますか？"),
        ConversationTurn(sequence=6, speaker="user", transcript="学費と奨学金制度はどうですか？"),
        # Recent turns
        ConversationTurn(sequence=7, speaker="assistant", transcript="奨学金は文科省や各大学の支援があります。"),
        ConversationTurn(sequence=8, speaker="user", transcript="申請締め切りはいつ頃ですか？"),
        ConversationTurn(sequence=9, speaker="assistant", transcript="通常は秋頃に受付が始まりますよ。"),
    ]

    selected = ContextBudgetManager.select_budgeted_turns(turns, max_turns=7, preserve_premise=True)
    assert len(selected) <= 7

    # First 2 premise turns must be preserved
    assert selected[0].sequence == 0
    assert selected[1].sequence == 1

    # Last 3 recent turns must be preserved
    assert selected[-3].sequence == 7
    assert selected[-2].sequence == 8
    assert selected[-1].sequence == 9

    # Result must remain strictly chronological
    sequences = [t.sequence for t in selected]
    assert sequences == sorted(sequences)


def test_select_budgeted_turns_budget_pressure():
    """Verify that when character budget is constrained, TextRank knapsack prunes low-density turns."""
    long_noisy_text = "無意味な文字列 " * 200  # ~1600 chars
    thematic_text = "日本語の敬語表現とビジネス会話の重要ポイントについて詳しく学びたいです。"

    turns = [
        ConversationTurn(sequence=i, speaker="user" if i % 2 == 0 else "assistant", transcript=thematic_text)
        for i in range(9)
    ]
    # Inject huge low-density noisy text at index 3
    turns[3].transcript = long_noisy_text

    selected = ContextBudgetManager.select_budgeted_turns(turns, max_turns=8)
    total_chars = sum(len(t.transcript or "") for t in selected)
    assert total_chars <= ContextBudgetManager.MAX_CONVERSATION_HISTORY_CHARS
    assert len(selected) <= 8

    # Sequences must be strictly chronological
    sequences = [t.sequence for t in selected]
    assert sequences == sorted(sequences)
