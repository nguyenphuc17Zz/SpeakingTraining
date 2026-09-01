"""Pipeline + integration tests."""

import pytest

from app.domains.monologue.analytics.pipeline import MonologuePipeline


@pytest.mark.asyncio
async def test_pipeline_basic():
    pipe = MonologuePipeline()
    words = [
        {"word": "私は", "start_ms": 0, "end_ms": 300, "confidence": 0.9},
        {"word": "学生", "start_ms": 600, "end_ms": 900, "confidence": 0.95},
        {"word": "です", "start_ms": 1100, "end_ms": 1300, "confidence": 0.98},
        {"word": "えーと", "start_ms": 1800, "end_ms": 2100, "confidence": 0.8},
        {"word": "趣味", "start_ms": 2400, "end_ms": 2700, "confidence": 0.9},
    ]
    res = await pipe.analyze_transcript(
        transcript="私は学生です。えーと、趣味は読書です。",
        words=words,
        speech_duration_ms=5000,
        target_duration_ms=60000,
        stt_confidence=0.9,
        audio_bytes=b"\x00"*12000,
        genre="opinion",
    )
    assert "pause_summary" in res
    assert "filler_summary" in res
    assert "fluency_timeline" in res
    assert len(res["fluency_timeline"]) >= 1
    assert res["speech_metrics_core"]["filler_count"] >= 1

@pytest.mark.asyncio
async def test_pipeline_empty():
    pipe = MonologuePipeline()
    res = await pipe.analyze_transcript(
        transcript="",
        words=[],
        speech_duration_ms=1000,
        target_duration_ms=60000,
        stt_confidence=0.9,
        audio_bytes=b"\x00"*12000,
        genre="opinion",
    )
    assert res["quality_gate"]["status"] in ("ok","LOW_CONFIDENCE","RETRY_AUDIO")

@pytest.mark.asyncio
async def test_evaluator_with_transcript_only(monkeypatch):
    # Transcript-only supported for office mode / broken mic
    from app.domains.monologue.evaluator import MonologueEvaluator
    import base64
    from unittest.mock import AsyncMock, patch
    from app.domains.speech.contracts import STTResult, WordTimestamp

    async def fake_evaluate(*args, **kwargs):
        return {"relevance":85,"coherence":80,"naturalness":82,"genre_fit":88,"confidence":0.9,"feedback":["Good"],"main_weakness":"conclusion"}

    async def fake_upgrade(*args, **kwargs):
        return {"minimal_correction":"私は学生です。","native_version":"私は学生です。","professional_version":None,"explanations":[]}

    evaluator = MonologueEvaluator(db=None)  # type: ignore
    evaluator.ai.evaluate = fake_evaluate  # type: ignore
    evaluator.ai.native_upgrade = fake_upgrade  # type: ignore
    dummy_ex = type("Ex", (), {"extra_metadata": {"speech_config": {"genre":"opinion","topic":"test","instruction":"話してください","constraints":[],"target_duration_sec":60}},"title":"test","instructions":"test"})()
    
    # transcript-only should evaluate successfully without audio
    res = await evaluator.evaluate(
        exercise=dummy_ex,
        user_transcript="私はテレワークに賛成です。",
        audio_base64=None,
        speech_metrics={"speech_duration_ms": 58000},
        target_duration_ms=60000,
        user_id="test",
    )
    assert res is not None
    assert res.get("status") == "ok" or res.get("score") is not None

    # Now with audio + mocked STT (audio required path)
    dummy_audio = base64.b64encode(b"\x00"*12000).decode()
    # Mock STT and quality gate
    async def fake_stt(audio_bytes, options=None):
        return STTResult(text="私はテレワークに賛成です。理由は時間が有効に使えるからです。例えば通勤が不要で家族と過ごせます。結論として良いと思います。", language="ja", duration_ms=58000, confidence=0.95, provider="test", words=[WordTimestamp(word="私は", start_ms=0, end_ms=300, confidence=0.9)], metadata={})
    # patch stt_router and quality
    orig_stt = evaluator.pipeline  # keep
    from app.domains.monologue import evaluator as eval_mod
    orig_transcribe = eval_mod.stt_router.transcribe
    eval_mod.stt_router.transcribe = fake_stt  # type: ignore
    from app.domains.audio.recording_service import AudioQualityAnalyzer
    orig_qa = AudioQualityAnalyzer.analyze
    def fake_qa(b):
        class R: has_clipping=False; snr_db=20; duration_ms=58000
        return R()
    AudioQualityAnalyzer.analyze = fake_qa  # type: ignore
    try:
        res = await evaluator.evaluate(
            exercise=dummy_ex,
            user_transcript="私はテレワークに賛成です。理由は時間が有効に使えるからです。例えば通勤が不要で家族と過ごせます。結論として良いと思います。",
            audio_base64=dummy_audio,
            speech_metrics={"speech_duration_ms": 58000},
            target_duration_ms=60000,
            user_id="test",
        )
        assert res["status"] == "completed"
        assert res["score"] > 0
        assert "assessment" in res
        assert res["metrics"]["speech_duration_ms"] == 58000
    finally:
        eval_mod.stt_router.transcribe = orig_transcribe  # type: ignore
        AudioQualityAnalyzer.analyze = orig_qa  # type: ignore
