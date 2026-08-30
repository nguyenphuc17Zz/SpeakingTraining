import pytest
from app.domains.reflex.exercise_factory import ReflexExerciseFactory
from app.domains.reflex.dictionary_pool import DICT_TRANSFORMATIONS


def test_reflex_transformation_category_filtering():
    """Verify that specifying a transformation category restricts generation to that category."""
    factory = ReflexExerciseFactory()

    # 1. Passive & Causative filter
    for _ in range(15):
        ex = factory.generate_transformation(transformation_category="passive_causative")
        assert ex["category"] == "passive_causative"
        assert ex["target_label"]
        assert ex["formula"]
        assert ex["grammar_note"]
        assert ex["source"]
        assert ex["expected"]

    # 2. Casual filter
    for _ in range(15):
        ex = factory.generate_transformation(transformation_category="casual")
        assert ex["category"] == "casual"
        assert ex["formula"]

    # 3. Conditional filter
    for _ in range(15):
        ex = factory.generate_transformation(transformation_category="conditional")
        assert ex["category"] == "conditional"

    # 4. Multi-category filter
    allowed = {"keigo", "advanced_modals"}
    for _ in range(20):
        ex = factory.generate_transformation(transformation_category="keigo,advanced_modals")
        assert ex["category"] in allowed

    # 5. 'all' generates across all categories
    seen_cats = set()
    for _ in range(30):
        ex = factory.generate_transformation(transformation_category="all")
        seen_cats.add(ex["category"])

    assert len(seen_cats) >= 3, f"Expected multiple categories in 'all' mode, got {seen_cats}"
