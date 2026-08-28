import pytest
from app.domains.shadowing.processing.segmenter import SentenceSegmenter
from app.domains.shadowing.processing.speaker_segmenter import SpeakerSegmenter


def test_segmenter_merges_short_sentence_fragments():
    raw_entries = [
        {"text": "今日は", "start": 0.0, "duration": 0.8},
        {"text": "とても天気が", "start": 0.9, "duration": 1.0},
        {"text": "いいですね。", "start": 2.0, "duration": 1.5},
    ]
    segments = SentenceSegmenter.segment_transcript(raw_entries, video_id="vid_test_1")
    assert len(segments) == 1
    assert "今日はとても天気がいいですね。" in segments[0].normalized_text
    assert segments[0].duration >= 3.0
    assert segments[0].reading is not None


def test_speaker_segmenter_extracts_labels():
    raw_entries = [
        {"text": "田中: おはようございます。", "start": 0.0, "duration": 2.0},
        {"text": "佐藤: おはようございます、いい天気ですね。", "start": 2.5, "duration": 3.0},
    ]
    segments = SentenceSegmenter.segment_transcript(raw_entries, video_id="vid_test_2")
    segments = SpeakerSegmenter.segment_speakers(segments)

    assert len(segments) == 2
    assert segments[0].speaker_id == "Speaker A"
    assert segments[0].normalized_text == "おはようございます。"
    assert segments[1].speaker_id == "Speaker B"
    assert "おはようございます、いい天気ですね。" in segments[1].normalized_text
