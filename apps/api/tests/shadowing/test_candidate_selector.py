import pytest
from app.domains.pronunciation.japanese.reading_resolver import JapaneseReadingResolver
from app.domains.shadowing.analysis.candidate_selector import ShadowingCandidateSelector
from app.domains.shadowing.contracts import (
    CandidateCategory,
    DifficultyReport,
    ExtractedGrammar,
    ExtractedVocabulary,
    NaturalExpression,
    SpeakingDifficulty,
    TranscriptSegmentDTO,
)


def _make_segment(seg_id: str, text: str, start: float, end: float, grammar=None, expressions=None, reading=None):
    dur = end - start
    hira_reading = reading or JapaneseReadingResolver.to_hiragana(text)
    return TranscriptSegmentDTO(
        id=seg_id,
        video_id="test_vid_123",
        start_time=start,
        end_time=end,
        duration=dur,
        text=text,
        normalized_text=text,
        reading=hira_reading,
        language="ja",
        confidence=1.0,
        speaker_id="Speaker A",
        sequence=0,
        difficulty=DifficultyReport(
            lexical_score=0.5,
            grammar_score=0.5,
            speed_mora_per_sec=6.0,
            pronunciation_complexity=0.5,
            sentence_density=0.5,
            context_naturalness=0.7,
            overall_difficulty=SpeakingDifficulty.NORMAL,
        ),
        vocabulary=[],
        grammar=grammar or [],
        expressions=expressions or [],
    )


def test_candidate_selector_prioritizes_long_vowels_for_pronunciation_weakness():
    # Segment 1: heavy long vowels (お父さん、東京、空港)
    seg1 = _make_segment("s1", "お父さんは東京の空港に向かいました。", 0.0, 4.5)

    # Segment 2: casual short sentence without long vowels
    seg2 = _make_segment("s2", "これは私の本です。", 5.0, 8.0)

    # When user has weakness in long vowels
    candidates = ShadowingCandidateSelector.select_candidates(
        segments=[seg1, seg2],
        learner_goals=["Daily conversation"],
        learner_weaknesses=[{"key": "pronunciation.long_vowels", "statement": "Yếu trường âm (long vowels)"}],
    )

    assert len(candidates) >= 1
    # Segment 1 should be the top recommendation
    assert candidates[0].segment_id == "s1"
    assert CandidateCategory.BEST_FOR_PRONUNCIATION in candidates[0].categories
    assert "trường âm" in candidates[0].reason or "long" in candidates[0].reason.lower()


def test_candidate_selector_prioritizes_keigo_for_workplace_goal():
    # Segment 1: polite keigo workplace sentence
    seg1 = _make_segment(
        "s1",
        "本日の資料につきまして、何卒よろしくお願い申し上げます。",
        0.0,
        5.2,
        grammar=[ExtractedGrammar(pattern="よろしくお願い申し上げます", level="N3", meaning="Xin nhờ giúp đỡ", context="Workplace")],
    )

    # Segment 2: casual slang
    seg2 = _make_segment(
        "s2",
        "マジでやばいじゃんそれ！",
        6.0,
        8.5,
        expressions=[NaturalExpression(expression="マジで", meaning="Thật á", category="slang", context_sentence="マジでやばいじゃんそれ！")],
    )

    # When user goal is workplace
    candidates = ShadowingCandidateSelector.select_candidates(
        segments=[seg1, seg2],
        learner_goals=["Workplace Japanese & Keigo (Tiếng Nhật công sở)"],
        learner_weaknesses=[],
    )

    assert len(candidates) >= 1
    assert candidates[0].segment_id == "s1"
    assert CandidateCategory.BEST_FOR_WORKPLACE in candidates[0].categories
    assert "kính ngữ" in candidates[0].reason or "công việc" in candidates[0].reason
