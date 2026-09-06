import pytest

from app.domains.conversation_intelligence.analyzers.entrainment_analyzer import (
    EntrainmentAnalyzer,
    EntrainmentLevel,
)


def test_register_detection_and_alignment():
    # Polite sentences
    assert EntrainmentAnalyzer.detect_register("明日は雨が降りますね。") == "polite"
    assert EntrainmentAnalyzer.detect_register("よろしくお願いいたします。") == "polite"

    # Casual sentences
    assert EntrainmentAnalyzer.detect_register("これ、めっちゃ美味しいじゃん！") == "casual"
    assert EntrainmentAnalyzer.detect_register("明日行くよ。") == "casual"

    # Aligned polite conversation
    res_aligned = EntrainmentAnalyzer.evaluate_alignment(
        partner_turns=["明日は何時に集合しますか？"],
        user_response="朝の九時に駅で集合しましょう。",
    )
    assert res_aligned.register_alignment_score >= 90.0
    assert res_aligned.partner_register == "polite"
    assert res_aligned.user_register == "polite"

    # Mismatched register (Casual slang in response to polite question)
    res_mismatched = EntrainmentAnalyzer.evaluate_alignment(
        partner_turns=["明日の会議の資料は完成しましたでしょうか？"],
        user_response="まだ出来てないじゃん。",
        target_register="polite",
    )
    assert res_mismatched.register_alignment_score <= 60.0
    assert res_mismatched.user_register == "casual"


def test_lexical_entrainment_keyword_echoing():
    partner_turns = [
        "こんにちは！",
        "今度の週末は新しい映画を見に行きませんか？",
    ]
    user_response = "いいですね！その映画、私もぜひ週末に見に行きたいです。"

    res = EntrainmentAnalyzer.evaluate_alignment(
        partner_turns=partner_turns,
        user_response=user_response,
    )

    assert "映画" in res.matched_lexical_primes
    assert "週末" in res.matched_lexical_primes
    assert res.lexical_entrainment_score >= 90.0
    assert res.overall_alignment_score >= 80.0
    assert res.entrainment_level == EntrainmentLevel.RESONANT_ENGAGED


def test_disconnected_response_detection():
    partner_turns = [
        "プロジェクトの進捗はいかがでしょうか？",
    ]
    user_response = "ラーメン食べたい。"

    res = EntrainmentAnalyzer.evaluate_alignment(
        partner_turns=partner_turns,
        user_response=user_response,
        target_register="polite",
    )

    assert len(res.matched_lexical_primes) == 0
    assert res.overall_alignment_score < 65.0
