import pytest

from app.domains.conversation_intelligence.analyzers.trp_turn_taking_analyzer import (
    TRPTurnTakingAnalyzer,
    TurnTransitionType,
)


def test_syntactic_trp_detection():
    # Complete polite sentence
    prob1 = TRPTurnTakingAnalyzer.evaluate_syntactic_trp("明日は雨が降ると思いますよ")
    assert prob1 >= 0.85

    # Clause boundary with conjunctive particle
    prob2 = TRPTurnTakingAnalyzer.evaluate_syntactic_trp("時間がないから")
    assert prob2 >= 0.85

    # Trailing-off conversational completion
    prob3 = TRPTurnTakingAnalyzer.evaluate_syntactic_trp("ちょっと気になるんだけど…")
    assert prob3 >= 0.85

    # Incomplete sentence cutting off at particle
    prob4 = TRPTurnTakingAnalyzer.evaluate_syntactic_trp("昨日買った本を")
    assert prob4 <= 0.35


def test_collaborative_overlap_vs_unwarranted_interruption():
    # Collaborative overlap: user begins 80ms before partner finishes, but partner's sentence is already at TRP
    res_overlap = TRPTurnTakingAnalyzer.evaluate_turn_transition(
        partner_utterance="それはとても素晴らしいですね",
        user_utterance="はい、本当にそう思います！",
        latency_ms=-80,
    )
    assert res_overlap.transition_type == TurnTransitionType.COLLABORATIVE_OVERLAP
    assert res_overlap.is_valid_turn_exchange is True
    assert res_overlap.turn_timing_score >= 85.0

    # Unwarranted interruption: user interrupts 400ms before incomplete clause
    res_interrupt = TRPTurnTakingAnalyzer.evaluate_turn_transition(
        partner_utterance="私の意見としては",
        user_utterance="いや、それは違います",
        latency_ms=-400,
    )
    assert res_interrupt.transition_type == TurnTransitionType.UNWARRANTED_INTERRUPTION
    assert res_interrupt.is_valid_turn_exchange is False
    assert res_interrupt.turn_timing_score < 60.0


def test_latency_windows_optimal_and_awkward_silence():
    # Native optimal latency 250ms
    res_optimal = TRPTurnTakingAnalyzer.evaluate_turn_transition(
        partner_utterance="週末は何をしましたか？",
        user_utterance="友達と映画を見に行きました。",
        latency_ms=250,
    )
    assert res_optimal.transition_type == TurnTransitionType.NATIVE_OPTIMAL
    assert res_optimal.turn_timing_score >= 95.0

    # Mild pause (800ms)
    res_mild = TRPTurnTakingAnalyzer.evaluate_turn_transition(
        partner_utterance="週末は何をしましたか？",
        user_utterance="ええと、本を読んでいました。",
        latency_ms=800,
    )
    assert res_mild.transition_type == TurnTransitionType.MILD_PAUSE
    assert 70.0 <= res_mild.turn_timing_score < 95.0

    # Awkward silence (1800ms)
    res_awkward = TRPTurnTakingAnalyzer.evaluate_turn_transition(
        partner_utterance="週末は何をしましたか？",
        user_utterance="何もしていません。",
        latency_ms=1800,
    )
    assert res_awkward.transition_type == TurnTransitionType.AWKWARD_DEAD_SILENCE
    assert res_awkward.turn_timing_score <= 60.0
