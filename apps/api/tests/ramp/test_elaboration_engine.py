"""Tests for ElaborationEngine (detection of short answers, missing reasons, missing examples)."""

import pytest
from app.domains.ramp.contracts import ElaborationSignal
from app.domains.ramp.elaboration_engine import ElaborationEngine


def test_detect_content_word_only():
    engine = ElaborationEngine()
    signals = engine.detect_signals(transcript="映画。", stage=3, measured_level="N4")
    assert ElaborationSignal.CONTENT_WORD_ONLY in signals or ElaborationSignal.TOO_SHORT in signals


def test_detect_full_sentence_success():
    engine = ElaborationEngine()
    transcript = "昨日は友達と一緒に映画を見に行きました。"
    signals = engine.detect_signals(transcript=transcript, stage=3, measured_level="N4")
    assert ElaborationSignal.CONTENT_WORD_ONLY not in signals
    assert ElaborationSignal.INCOMPLETE_SENTENCE not in signals
    assert ElaborationSignal.TOO_SHORT not in signals


def test_reason_detection_stage_5():
    engine = ElaborationEngine()
    # Response without reason markers at Stage 5
    without_reason = "週末はカフェで勉強しました。"
    signals = engine.detect_signals(transcript=without_reason, stage=5, measured_level="N3")
    assert ElaborationSignal.NO_REASON in signals

    # Response with reason marker から
    with_reason = "週末は試験が近いから、カフェで集中して勉強しました。"
    signals_ok = engine.detect_signals(transcript=with_reason, stage=5, measured_level="N3")
    assert ElaborationSignal.NO_REASON not in signals_ok


def test_example_detection_stage_6():
    engine = ElaborationEngine()
    # Response without example markers at Stage 6
    without_example = "旅行が好きです。新しい文化を体験できるからです。"
    signals = engine.detect_signals(transcript=without_example, stage=6, measured_level="N3")
    assert ElaborationSignal.NO_EXAMPLE in signals

    # Response with example marker 例えば
    with_example = "旅行が好きです。新しい文化を体験できるからです。例えば、去年京都へ行って歴史的なお寺を見学しました。"
    signals_ok = engine.detect_signals(transcript=with_example, stage=6, measured_level="N3")
    assert ElaborationSignal.NO_EXAMPLE not in signals_ok


def test_build_elaboration_prompt():
    engine = ElaborationEngine()
    signals = [ElaborationSignal.NO_REASON]
    prompt = engine.build_elaboration_prompt(signals, stage=5, step=2)
    assert prompt is not None
    assert prompt.signal == ElaborationSignal.NO_REASON
    assert "から" in prompt.cue_jp or "ので" in prompt.cue_jp
    assert prompt.step == 2


def test_build_retry_variation():
    engine = ElaborationEngine()
    original = "週末は何をしましたか？"
    variation_1 = engine.build_retry_variation(original, stage=4, attempt_number=1)
    variation_2 = engine.build_retry_variation(original, stage=4, attempt_number=2)
    assert isinstance(variation_1, str)
    assert isinstance(variation_2, str)
