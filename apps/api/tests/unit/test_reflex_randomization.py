import pytest
from app.domains.reflex.exercise_factory import ReflexExerciseFactory, _GLOBAL_RECENT_QNA, _QNA_SHUFFLE_QUEUE
from app.domains.reflex.dictionary_pool import DICT_QNA_QUESTIONS


def test_reflex_qna_randomization_no_repeats():
    """Verify that calling generate_qna 50 times produces 50 unique questions with 0% repeats."""
    factory = ReflexExerciseFactory()
    seen = []
    for _ in range(50):
        # Even if a new factory is instantiated each time (simulating HTTP requests)
        f = ReflexExerciseFactory()
        ex = f.generate_qna(difficulty="normal", pressure_level="normal")
        prompt = ex["prompt"]
        seen.append(prompt)

    # 50 consecutive calls from a 100+ pool must all be distinct
    unique_count = len(set(seen))
    assert unique_count == 50, f"Expected 50 unique prompts, but got {unique_count}. Repeats: {[p for p in seen if seen.count(p) > 1]}"


def test_reflex_transformation_and_context_variety():
    """Verify variety in transformation and context generators."""
    f = ReflexExerciseFactory()
    transforms = [f.generate_transformation()["prompt"] for _ in range(25)]
    contexts = [f.generate_context()["prompt"] for _ in range(14)]

    assert len(set(transforms)) == 25
    assert len(set(contexts)) == 14
