import pytest

from app.domains.pronunciation.contracts import MoraUnit
from app.domains.pronunciation.japanese.mora_analyzer import JapaneseMoraAnalyzer
from app.domains.pronunciation.japanese.sequence_alignment import JapaneseSequenceAligner
from app.domains.pronunciation.analyzers.phoneme_analyzer import PhonemeAnalyzer
from app.domains.pronunciation.contracts import AnalysisConfidenceLevel


def test_needleman_wunsch_exact_match():
    moras = JapaneseMoraAnalyzer.segment_moras("おはよう")
    user_kana = ["お", "は", "よ", "う"]
    aligned = JapaneseSequenceAligner.align(moras, user_kana)

    assert len(aligned) == 4
    for pair in aligned:
        assert pair.operation == "match"
        assert pair.similarity == 1.0


def test_needleman_wunsch_with_prefix_filler():
    """Learner says 'えーっと、おはよう' for target 'おはよう'.

    Before Needleman-Wunsch, naive index matching would compare 'お' with 'え' and misalign everything.
    Now, 'えーっと' is identified as insertions and 'おはよう' is matched 100%!
    """
    moras = JapaneseMoraAnalyzer.segment_moras("おはよう")
    # User adds filler: え, ー, っ, と before おはよう
    user_kana = ["え", "ー", "っ", "と", "お", "は", "よ", "う"]
    aligned = JapaneseSequenceAligner.align(moras, user_kana)

    target_pairs = [p for p in aligned if p.target_mora is not None]
    assert len(target_pairs) == 4

    for p in target_pairs:
        assert p.operation == "match"
        assert p.user_kana == p.target_mora.kana

    # Also verify PhonemeAnalyzer gives high score rather than 0
    comp, assessments = PhonemeAnalyzer.analyze(
        target_moras=moras,
        user_transcript="えーっと、おはよう",
        alignment_confidence=AnalysisConfidenceLevel.HIGH,
    )
    assert comp.score >= 90.0


def test_needleman_wunsch_voicing_substitution():
    moras = JapaneseMoraAnalyzer.segment_moras("がっこう")
    # Learner says 'かっこう' (か instead of が)
    user_kana = ["か", "っ", "こ", "う"]
    aligned = JapaneseSequenceAligner.align(moras, user_kana)

    assert len(aligned) == 4
    assert aligned[0].operation == "substitution"
    assert aligned[0].target_mora.kana == "が"
    assert aligned[0].user_kana == "か"
    assert aligned[0].similarity == 0.75  # Voicing pair score


def test_needleman_wunsch_mora_omission():
    moras = JapaneseMoraAnalyzer.segment_moras("ありがとう")
    # Learner drops 'り': 'あがとう' -> 'あ', 'が', 'と', 'う'
    user_kana = ["あ", "と", "う"]
    aligned = JapaneseSequenceAligner.align(moras, user_kana)

    target_pairs = [p for p in aligned if p.target_mora is not None]
    assert len(target_pairs) == len(moras)
    deleted = [p for p in target_pairs if p.operation == "deletion"]
    assert len(deleted) >= 1
