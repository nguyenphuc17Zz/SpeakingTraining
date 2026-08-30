import pytest
from app.domains.reflex.exercise_factory import ReflexExerciseFactory
from app.domains.reflex.dictionary_pool import DICT_QNA_QUESTIONS


def test_reflex_qna_topic_filtering():
    """Verify that specifying a topic restricts generation to only that topic."""
    factory = ReflexExerciseFactory()

    # 1. Interview topic filter
    for _ in range(15):
        ex = factory.generate_qna(topic="interview")
        assert ex["category"] == "interview"
        assert ex["topic"] == "interview"
        assert len(ex["key_vocab"]) >= 1
        assert "multi_answers" in ex
        assert "positive" in ex["multi_answers"]
        assert "negative" in ex["multi_answers"]
        assert "extended" in ex["multi_answers"]

    # 2. Daily topic filter
    for _ in range(15):
        ex = factory.generate_qna(topic="daily")
        assert ex["category"] == "daily"
        assert len(ex["idea_sparks"]) >= 1

    # 3. Multi-topic filter (comma-separated)
    allowed = {"daily", "workplace"}
    for _ in range(20):
        ex = factory.generate_qna(topic="daily,workplace")
        assert ex["category"] in allowed

    # 4. 'all' topic generates from all categories
    seen_categories = set()
    for _ in range(30):
        ex = factory.generate_qna(topic="all")
        seen_categories.add(ex["category"])

    assert len(seen_categories) >= 3, f"Expected variety of categories in 'all' mode, got {seen_categories}"
