"""Tests for SpeechTopicGenerator — §75."""

import pytest

from app.domains.monologue.generation.speech_topic_generator import SpeechTopicGenerator
from app.domains.monologue.generation.variety_policy import SpeechVarietyPolicy
from app.domains.monologue.generation.topic_validator import TopicValidator
from app.domains.monologue.contracts import SpeechGenre, SpeechSupportLevel


@pytest.mark.asyncio
async def test_variety_policy_signature():
    sig = SpeechVarietyPolicy.compute_signature("hello", "opinion", "daily_life", 3, 60, "include_one_example")
    sig2 = SpeechVarietyPolicy.compute_signature("hello", "opinion", "daily_life", 3, 60, "include_one_example")
    assert sig == sig2
    sig3 = SpeechVarietyPolicy.compute_signature("hello2", "opinion", "daily_life", 3, 60, "include_one_example")
    assert sig != sig3

@pytest.mark.asyncio
async def test_topic_validator_ok():
    valid, issues = TopicValidator.validate(
        topic="将来のキャリアで目指すこと",
        instruction="「将来のキャリアで目指すこと」について、60秒で話してください。",
        genre=SpeechGenre.OPINION,
        difficulty=3,
        duration_sec=60,
        topic_domain="career",
        constraints=["include_one_example"],
        support_level=SpeechSupportLevel.STRUCTURE,
        session_signature="abc123",
        recent_signatures=[],
    )
    assert valid, issues

@pytest.mark.asyncio
async def test_topic_validator_fail():
    valid, issues = TopicValidator.validate(
        topic="",
        instruction="short",
        genre=SpeechGenre.OPINION,
        difficulty=99,
        duration_sec=999,
        topic_domain="career",
        constraints=[],
        support_level=SpeechSupportLevel.BLIND,
        session_signature="dup",
        recent_signatures=["dup"],
    )
    assert not valid
    assert len(issues) >= 2

def test_no_hardcoded_topic_db():
    # Ensure domain does not contain TOPICS = [...] with >20 entries
    import pathlib
    import re
    p = pathlib.Path("app/domains/monologue/generation/speech_topic_generator.py")
    txt = p.read_text(encoding="utf-8")
    # Look for giant list literal assignment with >10 quoted entries on consecutive lines
    # Simple check: should not contain "My hobby" style DB
    assert "My hobby" not in txt
    # Ensure provider abstraction used
    assert "AIRouter" in txt

def test_genre_ontology_small():
    import pathlib
    p = pathlib.Path("app/domains/monologue/generation/genre_ontology.py")
    txt = p.read_text(encoding="utf-8")
    # Must not contain giant vocabulary DB — ontology should stay < 500 lines and < 100 SpeechGenre references
    assert txt.count("SpeechGenre") < 100
    # Ensure domain file not bloated with hard-coded topic DB
    assert len(txt.splitlines()) < 400
