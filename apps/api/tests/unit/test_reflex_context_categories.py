import pytest
from app.domains.reflex.exercise_factory import ReflexExerciseFactory
from app.domains.reflex.dictionary_pool import DICT_CONTEXTS


def test_reflex_context_category_filtering():
    factory = ReflexExerciseFactory()

    # Test single category
    wp_ex = factory.generate_context(context_category="workplace")
    assert wp_ex["category"] == "workplace"
    assert wp_ex["intent"] is not None
    assert wp_ex["speaker_ja"] is not None
    assert len(wp_ex["key_vocab"]) > 0
    assert len(wp_ex["idea_sparks"]) > 0

    # Test business category
    biz_ex = factory.generate_context(context_category="business_client")
    assert biz_ex["category"] == "business_client"
    assert biz_ex["role"] in ["Khách hàng", "Đối tác"]

    # Test all / random
    all_ex = factory.generate_context(context_category="all")
    assert all_ex["category"] in ["workplace", "business_client", "apology_emergency", "social_casual", "service_dining"]
    assert all_ex["sample_answer"] is not None
