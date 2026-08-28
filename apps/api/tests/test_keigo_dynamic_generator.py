import pytest
from app.domains.keigo.dynamic_generator import AIKeigoGenerator, BUSINESS_TOPICS_POOL
from app.domains.keigo.exercise_factory import KeigoExerciseFactory

def test_business_topics_pool_not_empty():
    assert len(BUSINESS_TOPICS_POOL) >= 15
    for topic, desc in BUSINESS_TOPICS_POOL:
        assert topic
        assert desc

@pytest.mark.asyncio
async def test_keigo_generator_fallback_structure():
    gen = AIKeigoGenerator(db=None)
    sub_modes = [
        "keigo_sonkeigo",
        "keigo_kenjougo",
        "keigo_teineigo",
        "keigo_transformation",
        "keigo_context",
        "keigo_doctor",
        "keigo_naturalness",
    ]
    for sub in sub_modes:
        ex = await gen.generate_dynamic_exercise(sub_mode=sub)
        assert "title" in ex
        assert "prompt" in ex
        assert "canonical" in ex
        assert "timer_limit_ms" in ex
