from unittest.mock import MagicMock, patch

import pytest

from app.domains.speech.adapters.faster_whisper import FasterWhisperAdapter
from app.domains.speech.contracts import STTOptions


def test_faster_whisper_hardware_detection():
    device, compute = FasterWhisperAdapter._detect_hardware("auto", "auto")
    assert device in ("cpu", "cuda")
    assert compute in ("int8", "float16", "float32")


@pytest.mark.asyncio
async def test_faster_whisper_empty_audio():
    adapter = FasterWhisperAdapter()
    result = await adapter.transcribe(b"")
    assert result.text == ""
    assert result.duration_ms == 0
    assert result.provider == "faster_whisper"


@pytest.mark.asyncio
async def test_faster_whisper_transcribe_mocked():
    adapter = FasterWhisperAdapter()

    mock_segment = MagicMock()
    mock_segment.text = "こんにちは"
    mock_segment.avg_logprob = -0.1
    mock_word = MagicMock()
    mock_word.word = "こんにちは"
    mock_word.start = 0.0
    mock_word.end = 0.6
    mock_word.probability = 0.99
    mock_segment.words = [mock_word]

    mock_info = MagicMock()
    mock_info.duration = 1.2
    mock_info.language_probability = 0.98

    mock_model = MagicMock()
    mock_model.transcribe.return_value = ([mock_segment], mock_info)

    with patch.object(adapter, "_get_or_load_model", return_value=mock_model):
        result = await adapter.transcribe(
            b"fake_audio_bytes_1234567890" * 10,
            options=STTOptions(model="base"),
        )
        assert result.text == "こんにちは"
        assert result.duration_ms == 1200
        assert len(result.words) == 1
        assert result.words[0].word == "こんにちは"
