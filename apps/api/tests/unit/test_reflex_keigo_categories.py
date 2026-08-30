"""Unit tests for Keigo Word Blitz (reflex_keigo_vocab) categories, formulas, subject ownership cues, and keyword search."""

import pytest
from app.domains.reflex.exercise_factory import ReflexExerciseFactory
from app.domains.keigo.keigo_vocab_pool import (
    get_all_keigo_vocab,
    get_sonkeigo_pool,
    get_kenjougo_pool,
    get_rule_based_pool,
    get_business_vocab_pool,
    search_keigo,
)


def test_keigo_pool_categories():
    """Verify that Keigo pool contains entries for all 4 practical categories."""
    all_words = get_all_keigo_vocab()
    assert len(all_words) >= 30

    sonkeigo = get_sonkeigo_pool()
    assert len(sonkeigo) >= 10

    kenjougo = get_kenjougo_pool()
    assert len(kenjougo) >= 10

    rule_based = get_rule_based_pool()
    assert len(rule_based) >= 5

    business = get_business_vocab_pool()
    assert len(business) >= 10


def test_keigo_search():
    """Verify keyword search finds matching keigo pairs."""
    results_eat = search_keigo("ăn")
    assert len(results_eat) >= 2
    assert any(k.canonical == "召し上がる" for k in results_eat)
    assert any(k.canonical == "いただく" for k in results_eat)

    results_biz = search_keigo("弊社")
    assert len(results_biz) >= 1


def test_generate_keigo_vocabulary_enriched():
    """Verify that generate_keigo_vocabulary outputs formula, subject_hint_vi, and example sentences."""
    factory = ReflexExerciseFactory()

    # 1. Sonkeigo category
    ex_sonkei = factory.generate_keigo_vocabulary(keigo_category="sonkeigo")
    assert "👑" in ex_sonkei["title"]
    assert ex_sonkei["target_type"] == "sonkeigo"
    assert "subject_hint_vi" in ex_sonkei
    assert "example_ja" in ex_sonkei
    assert "example_vi" in ex_sonkei
    assert "formula" in ex_sonkei

    # 2. Kenjougo category
    ex_kenjou = factory.generate_keigo_vocabulary(keigo_category="kenjougo")
    assert "🙇" in ex_kenjou["title"]
    assert ex_kenjou["target_type"] == "kenjougo"
    assert "subject_hint_vi" in ex_kenjou

    # 3. Custom Keyword Search Filter
    ex_custom = factory.generate_keigo_vocabulary(keigo_category="ăn")
    assert ex_custom["canonical"] in ("召し上がる", "いただく")
