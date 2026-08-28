import pytest

from app.domains.speech.contracts import (
    STTComputeType,
    STTDevice,
    STTOptions,
    STTResult,
    TTSAudioOutput,
    TTSOptions,
    WordTimestamp,
)
from app.domains.speech.stt_router import stt_router
from app.domains.speech.tts_router import tts_router


def test_stt_options_and_result_contracts():
    opts = STTOptions(
        model="small",
        device=STTDevice.CPU,
        compute_type=STTComputeType.INT8,
        language="ja",
    )
    assert opts.model == "small"
    assert opts.language == "ja"

    word = WordTimestamp(word="こんにちは", start_ms=0, end_ms=500, confidence=0.98)
    res = STTResult(
        text="こんにちは",
        language="ja",
        duration_ms=500,
        confidence=0.98,
        processing_time_ms=120,
        model="small",
        provider="faster_whisper",
        words=[word],
    )
    assert res.text == "こんにちは"
    assert len(res.words) == 1
    assert res.words[0].word == "こんにちは"


def test_tts_options_and_output_contracts():
    opts = TTSOptions(voice_id="2", speed=1.1, pitch=0.05)
    assert opts.voice_id == "2"
    assert opts.speed == 1.1

    output = TTSAudioOutput(
        audio_bytes=b"RIFFdummydata",
        format="wav",
        duration_ms=1200,
        voice="2",
        provider="voicevox",
        processing_time_ms=85,
    )
    assert output.duration_ms == 1200
    assert output.format == "wav"


def test_stt_router_models_recommendation():
    models = stt_router.get_available_models()
    assert len(models) >= 5
    model_ids = [m["id"] for m in models]
    assert "base" in model_ids
    assert "tiny" in model_ids
    assert "turbo" in model_ids


@pytest.mark.asyncio
async def test_tts_router_fallback_voices():
    voices = await tts_router.get_available_voices()
    assert len(voices) > 0
    assert any("ずんだもん" in v.name or "Zundamon" in v.name for v in voices)
