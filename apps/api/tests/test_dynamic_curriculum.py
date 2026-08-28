import pytest
from app.domains.learning.dynamic_curriculum import AICurriculumGenerator, LEVEL_LABELS, GOAL_LABELS


def test_curriculum_labels():
    assert len(LEVEL_LABELS) >= 5
    assert "beginner" in LEVEL_LABELS
    assert "intermediate" in LEVEL_LABELS
    assert len(GOAL_LABELS) >= 5
    assert "workplace" in GOAL_LABELS
    assert "baito" in GOAL_LABELS


def test_fallback_curriculum_structure():
    gen = AICurriculumGenerator(db=None)
    fallback = gen._build_fallback_curriculum(level="intermediate", target_goal="workplace", daily_minutes=30)
    assert "stages" in fallback
    assert len(fallback["stages"]) == 4
    for st in fallback["stages"]:
        assert "nodes" in st
        assert len(st["nodes"]) >= 3
        for node in st["nodes"]:
            assert "id" in node
            assert "title" in node
            assert "target_mode" in node
            assert node["target_mode"].startswith("/")
