from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.speech.adapters.voicevox import VoicevoxAdapter
from app.domains.speech.contracts import TTSOptions
from app.domains.speech.errors import TTSUnavailableError


@pytest.mark.asyncio
async def test_voicevox_empty_text():
    adapter = VoicevoxAdapter()
    output = await adapter.synthesize("")
    assert output.audio_bytes == b""
    assert output.duration_ms == 0


@pytest.mark.asyncio
async def test_voicevox_engine_offline_fallback():
    # If VOICEVOX is offline on localhost, get_available_voices returns fallback catalog
    adapter = VoicevoxAdapter(engine_url="http://127.0.0.1:59999", timeout_seconds=0.1)
    voices = await adapter.get_available_voices()
    assert len(voices) > 0

    # synthesize raises TTSUnavailableError
    with pytest.raises(TTSUnavailableError):
        await adapter.synthesize("こんにちは", options=TTSOptions())


@pytest.mark.asyncio
async def test_voicevox_mocked_synthesis():
    adapter = VoicevoxAdapter()

    fake_query = {"kana": "コンニチワ", "speedScale": 1.0, "pitchScale": 0.0}
    fake_wav = b"RIFF" + b"\x00" * 48000  # ~1 second WAV data

    mock_client = AsyncMock()
    mock_query_resp = MagicMock(status_code=200)
    mock_query_resp.json.return_value = fake_query

    mock_synth_resp = MagicMock(status_code=200, content=fake_wav)

    mock_client.post.side_effect = [mock_query_resp, mock_synth_resp]
    mock_client.__aenter__.return_value = mock_client

    with patch.object(adapter, "_get_client", return_value=mock_client):
        output = await adapter.synthesize("こんにちは", options=TTSOptions(voice_id="1", speed=1.1))
        assert output.audio_bytes == fake_wav
        assert output.duration_ms is not None
        assert output.duration_ms > 0
        assert output.provider == "voicevox"
