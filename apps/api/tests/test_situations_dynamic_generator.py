import pytest
from app.domains.situations.dynamic_generator import SITUATIONAL_CATEGORIES, INFINITE_RANDOM_SEEDS
from app.domains.situations.scenario_generator import ScenarioGenerator


def test_situational_categories_completeness():
    assert len(SITUATIONAL_CATEGORIES) >= 6
    expected_cats = ["food", "retail", "transportation", "healthcare", "workplace", "travel"]
    for cat in expected_cats:
        assert cat in SITUATIONAL_CATEGORIES
        info = SITUATIONAL_CATEGORIES[cat]
        assert "ja" in info and len(info["ja"]) > 0
        assert "locations" in info and len(info["locations"]) > 0
        assert "roles" in info and len(info["roles"]) > 0


def test_infinite_random_seeds():
    assert len(INFINITE_RANDOM_SEEDS) >= 10
    for seed in INFINITE_RANDOM_SEEDS:
        assert "loc" in seed
        assert "role" in seed
        assert "topic" in seed


def test_scenario_generator_fallback():
    gen = ScenarioGenerator()
    sc = gen.generate(category="food", difficulty="normal", duration_minutes=5)
    assert "location" in sc
    assert "actors" in sc
    assert "goals" in sc
    assert len(sc["goals"]) > 0
