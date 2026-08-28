import pytest
from app.domains.pitch.dynamic_generator import AIPitchGenerator, PITCH_TOPICS_POOL
from app.domains.pitch.exercise_factory import PitchExerciseFactory


def test_pitch_topics_pool():
    assert len(PITCH_TOPICS_POOL) >= 5
    for topic, sub in PITCH_TOPICS_POOL:
        assert isinstance(topic, str) and len(topic) > 0
        assert isinstance(sub, str) and len(sub) > 0


def test_pitch_factory_all_submodes():
    factory = PitchExerciseFactory()
    
    # 1. Minimal pair
    mp = factory.generate_minimal_pair()
    assert "canonical" in mp
    assert "prompt" in mp
    assert "pair" in mp
    
    # 2. Mora length
    mora = factory.generate_mora_length()
    assert "canonical" in mora
    assert "short_mora" in mora
    assert "long_mora" in mora

    # 3. Devoicing
    dev = factory.generate_devoicing()
    assert "canonical" in dev
    assert "prompt" in dev

    # 4. Contour
    cnt = factory.generate_contour()
    assert "canonical" in cnt
    assert "pattern" in cnt

    # 5. Recognition
    rec = factory.generate_recognition()
    assert "canonical" in rec
