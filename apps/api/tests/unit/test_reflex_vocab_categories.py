"""Unit tests for Vocabulary Blitz (reflex_vocabulary) categorization & keyword search without N5-N1 divisions."""

import pytest
from app.domains.reflex.exercise_factory import ReflexExerciseFactory
from app.domains.reflex.vocab_pool import (
    get_all_vocab_words,
    get_vocab_by_category,
    search_vocab,
)


def test_vocab_pool_categories():
    """Verify that vocabulary pool is populated across all 5 practical categories."""
    all_words = get_all_vocab_words()
    assert len(all_words) >= 60

    action_verbs = get_vocab_by_category("action_verbs")
    assert len(action_verbs) >= 15

    emotions_adj = get_vocab_by_category("emotions_adj")
    assert len(emotions_adj) >= 15

    adverbs = get_vocab_by_category("adverbs_mimetic")
    assert len(adverbs) >= 15

    workplace = get_vocab_by_category("workplace_biz")
    assert len(workplace) >= 15

    daily = get_vocab_by_category("daily_life")
    assert len(daily) >= 15


def test_vocab_keyword_search():
    """Verify search_vocab finds matching words by keyword."""
    results = search_vocab("liên lạc")
    assert len(results) >= 1
    assert any(w.word == "連絡する" for w in results)

    results_colloc = search_vocab("LINE")
    assert len(results_colloc) >= 1


def test_generate_vocabulary_spoken_japanese():
    """Verify that generate_vocabulary outputs 100% Japanese spoken response challenge."""
    factory = ReflexExerciseFactory()

    # 1. Action Verbs
    ex_action = factory.generate_vocabulary(vocab_category="action_verbs")
    assert ex_action["direction"] == "vi_to_ja"
    assert ex_action["category"] == "action_verbs"
    assert "collocation_ja" in ex_action
    assert "example_ja" in ex_action
    assert ex_action["canonical"] == ex_action["word"]

    # 2. Mimetic / Adverbs
    ex_adv = factory.generate_vocabulary(vocab_category="adverbs_mimetic")
    assert ex_adv["category"] == "adverbs_mimetic"
    assert ex_adv["word"]

    # 3. Custom Keyword Search Filter
    ex_custom = factory.generate_vocabulary(vocab_category="liên lạc")
    assert ex_custom["word"] == "連絡する"
    assert ex_custom["collocation_ja"] == "連絡を取る"
