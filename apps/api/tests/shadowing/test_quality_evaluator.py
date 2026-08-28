import pytest
from app.domains.shadowing.contracts import TranscriptQuality
from app.domains.shadowing.processing.quality_evaluator import TranscriptQualityEvaluator


def test_evaluate_high_quality_japanese_transcript():
    segments = [
        {"text": "こんにちは、本日のニュースをお伝えします。", "start": 0.0, "end": 3.5},
        {"text": "東京では桜が満開を迎えました。", "start": 3.8, "end": 7.0},
        {"text": "週末はお花見日和になる見込みです。", "start": 7.2, "end": 11.0},
    ]
    report = TranscriptQualityEvaluator.evaluate_transcript(segments)
    assert report.quality == TranscriptQuality.HIGH
    assert report.language == "Japanese"
    assert report.has_timestamps is True
    assert report.confidence >= 0.85
    assert len(report.issues) == 0


def test_evaluate_non_japanese_transcript():
    segments = [
        {"text": "Hello, welcome to our daily news show.", "start": 0.0, "end": 3.0},
        {"text": "Today we are discussing foreign politics.", "start": 3.2, "end": 6.5},
    ]
    report = TranscriptQualityEvaluator.evaluate_transcript(segments)
    assert report.quality == TranscriptQuality.LOW
    assert report.language == "Non-Japanese"
    assert any("not appear to be Japanese" in issue for issue in report.issues)


def test_evaluate_empty_transcript():
    report = TranscriptQualityEvaluator.evaluate_transcript([])
    assert report.quality == TranscriptQuality.LOW
    assert report.has_timestamps is False
