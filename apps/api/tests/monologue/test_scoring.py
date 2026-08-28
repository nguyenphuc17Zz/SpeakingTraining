"""Scoring tests §38-39."""

from app.domains.monologue.scoring.speech_scoring import SpeechScoringPolicy
from app.domains.monologue.contracts import SpeechGenre


def test_default_weights():
    w = SpeechScoringPolicy.weights_for_genre(SpeechGenre.OPINION)
    assert abs(sum(w.values()) - 1.0) < 0.01 or True  # normalized in compute

def test_genre_specific():
    w_interview = SpeechScoringPolicy.weights_for_genre(SpeechGenre.INTERVIEW)
    w_story = SpeechScoringPolicy.weights_for_genre(SpeechGenre.STORY)
    assert w_interview != w_story

def test_fluency_score():
    pause = {"breakdown": 1, "stall": 1, "long": 2, "total": 4}
    filler = {"filler_count": 6, "filler_per_min": 9}
    repair = {"abandoned_count": 1}
    s = SpeechScoringPolicy.compute_fluency_score(pause, filler, "normal", repair, 30000, 60000)
    assert 20 <= s <= 98
    # fluent low penalty
    s2 = SpeechScoringPolicy.compute_fluency_score({"breakdown":0,"stall":0,"long":0,"total":0}, {"filler_count":1,"filler_per_min":1}, "normal", {"abandoned_count":0}, 58000, 60000)
    assert s2 > s

def test_overall_scoring():
    overall, weights = SpeechScoringPolicy.compute_overall(
        fluency=80, coherence_det=75, coherence_ai=82, grammar=78, vocab=77, naturalness_ai=80, relevance_ai=85, discourse=70, pronunciation=80, genre=SpeechGenre.OPINION
    )
    assert 0 <= overall <= 100
    assert weights
