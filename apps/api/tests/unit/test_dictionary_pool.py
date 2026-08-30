import pytest
from app.domains.reflex.dictionary_pool import (
    N5_VERBS,
    N4_VERBS,
    N3_VERBS,
    N2_VERBS,
    N1_VERBS,
    EASY_VERBS,
    NORMAL_VERBS,
    HARD_VERBS,
    ALL_DICT_VERBS,
)
from app.domains.reflex.conjugation_engine import JapaneseConjugationEngine, ConjugationForm
from app.domains.reflex.exercise_factory import ReflexExerciseFactory


def test_dictionary_pool_size():
    """Verify dictionary pool has 600+ verbs across N5-N1."""
    assert len(N5_VERBS) >= 120, "N5 verbs should be at least 120"
    assert len(N4_VERBS) >= 130, "N4 verbs should be at least 130"
    assert len(N3_VERBS) >= 130, "N3 verbs should be at least 130"
    assert len(N2_VERBS) >= 110, "N2 verbs should be at least 110"
    assert len(N1_VERBS) >= 70, "N1 verbs should be at least 70"
    assert len(ALL_DICT_VERBS) >= 600, f"Total verbs should be >= 600, got {len(ALL_DICT_VERBS)}"


def test_conjugation_engine_compatibility():
    """Verify all verbs can be conjugated into multiple forms without raising exceptions."""
    engine = JapaneseConjugationEngine()
    test_forms = [
        ConjugationForm.NAI,
        ConjugationForm.TA,
        ConjugationForm.TE,
        ConjugationForm.POTENTIAL,
        ConjugationForm.PASSIVE,
        ConjugationForm.CAUSATIVE,
        ConjugationForm.CAUSATIVE_PASSIVE,
        ConjugationForm.VOLITIONAL,
        ConjugationForm.BA,
        ConjugationForm.TARA,
        ConjugationForm.IMPERATIVE,
    ]

    for item in ALL_DICT_VERBS[:50]:  # sample test
        for form in test_forms:
            res = engine.conjugate(item.verb, form)
            assert res.canonical, f"Canonical form empty for {item.verb} in {form}"


def test_exercise_factory_conjugation_generation():
    """Verify exercise factory picks from the expanded pool and includes jlpt_level."""
    factory = ReflexExerciseFactory()
    ex = factory.generate_conjugation(difficulty="hard", pressure_level="blitz")
    assert ex["prompt"]
    assert ex["target"]
    assert "jlpt_level" in ex
