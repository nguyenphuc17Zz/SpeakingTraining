import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.infrastructure.database.base import Base
from app.domains.users.models import User
from app.domains.learner_memory.models import LearnerProfile
from app.domains.monologue.service import MonologueService
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

@pytest.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()

@pytest.mark.asyncio
async def test_monologue_generate_fallback_when_ai_down(test_db):
    # Hard error per user choice: no fallback, should raise 503
    user = User(id="u_mono_1", display_name="Test", locale="ja-JP")
    test_db.add(user)
    prof = LearnerProfile(user_id="u_mono_1", overall_level="N3", speaking_level="N3", confidence_score=0.5, level_confidence="medium", total_sessions_analyzed=0, total_turns_analyzed=0)
    test_db.add(prof)
    await test_db.commit()
    from app.domains.monologue.generation import speech_topic_generator as stg_mod
    orig = stg_mod.AIRouter
    class FailingRouter:
        def __init__(self, db): pass
        async def generate(self, task, request, user_id):
            raise Exception("AI down simulated")
    stg_mod.AIRouter = FailingRouter
    try:
        svc = MonologueService(test_db)
        try:
            await svc.generate_exercise(user_id="u_mono_1", duration_sec=60, genre="opinion")
            assert False, "Should have raised RuntimeError for AI down (no fallback)"
        except RuntimeError as e:
            assert "AI" in str(e) or "failed" in str(e).lower()
    finally:
        stg_mod.AIRouter = orig

@pytest.mark.asyncio
async def test_monologue_evaluate_transcript_only(test_db):
    # Audio-only enforced: transcript-only should hard fail
    user = User(id="u_mono_2", display_name="Test2", locale="ja-JP")
    test_db.add(user)
    prof = LearnerProfile(user_id="u_mono_2", overall_level="N3", speaking_level="N3", confidence_score=0.5, level_confidence="medium", total_sessions_analyzed=0, total_turns_analyzed=0)
    test_db.add(prof)
    await test_db.commit()
    from app.domains.monologue.generation import speech_topic_generator as stg_mod
    orig = stg_mod.AIRouter
    class SuccessRouter:
        def __init__(self, db): pass
        async def generate(self, task, request, user_id):
            from unittest.mock import MagicMock
            m = MagicMock()
            m.text = '{"topic":"テレワーク","instruction":"「テレワーク」について60秒で話してください。","constraints":["include_one_example"],"keywords":[],"outline":[],"difficulty":3,"expected_duration_sec":30,"prep_duration_sec":15}'
            m.provider = "test"; m.model = "test"
            return m
    stg_mod.AIRouter = SuccessRouter
    from app.domains.monologue.ai import analyzer as ai_mod
    orig_eval = ai_mod.MonologueAIAnalyzer.evaluate
    orig_up = ai_mod.MonologueAIAnalyzer.native_upgrade
    async def fake_eval(self, *a, **kw):
        return {"relevance": 88, "coherence": 82, "naturalness": 80, "genre_fit": 85, "confidence": 0.9, "feedback": ["Good structure"], "main_strength": "clear", "main_weakness": "conclusion"}
    async def fake_up(self, *a, **kw):
        return {"minimal_correction": "私は学生です。", "native_version": "私は学生です。自然です。", "professional_version": None, "explanations": []}
    ai_mod.MonologueAIAnalyzer.evaluate = fake_eval
    ai_mod.MonologueAIAnalyzer.native_upgrade = fake_up
    try:
        svc = MonologueService(test_db)
        ex = await svc.generate_exercise(user_id="u_mono_2", duration_sec=30)
        # transcript-only should raise ValueError (audio required)
        try:
            await svc.evaluate_exercise(
                exercise_id=ex.id,
                user_id="u_mono_2",
                user_transcript="私はテレワークに賛成です。",
                audio_base64=None,
                speech_metrics={"speech_duration_ms": 28000, "target_duration_ms": 30000},
            )
            assert False, "Should have raised for missing audio"
        except ValueError as e:
            assert "Audio is required" in str(e)
        # Now with dummy audio (mock STT)
        from unittest.mock import patch
        import base64
        dummy_audio = base64.b64encode(b"\x00"*12000).decode()
        # Mock STT to avoid real model
        from app.domains.monologue import evaluator as eval_mod
        orig_stt = eval_mod.stt_router.transcribe
        async def fake_stt(audio_bytes, options=None):
            from app.domains.speech.contracts import STTResult, WordTimestamp
            return STTResult(text="私はテレワークに賛成です。理由は時間が有効に使えるからです。例えば通勤が不要で家族と過ごせます。結論として良いと思います。", language="ja", duration_ms=28000, confidence=0.95, provider="test", words=[WordTimestamp(word="私は", start_ms=0, end_ms=300, confidence=0.9), WordTimestamp(word="賛成", start_ms=500, end_ms=900, confidence=0.9)], metadata={})
        eval_mod.stt_router.transcribe = fake_stt
        # Mock AudioQualityAnalyzer to return ok
        from app.domains.audio.recording_service import AudioQualityAnalyzer
        orig_qa = AudioQualityAnalyzer.analyze
        def fake_qa(b):
            class R: has_clipping=False; snr_db=20; duration_ms=28000
            return R()
        AudioQualityAnalyzer.analyze = fake_qa  # type: ignore
        try:
            result = await svc.evaluate_exercise(
                exercise_id=ex.id,
                user_id="u_mono_2",
                user_transcript="私はテレワークに賛成です。理由は時間が有効に使えるからです。例えば通勤が不要で家族と過ごせます。結論として良いと思います。",
                audio_base64=dummy_audio,
                speech_metrics={"speech_duration_ms": 28000, "target_duration_ms": 30000},
            )
            assert result["score"] > 0
            assert result["assessment"]["overall"] > 0
            assert "fluency_timeline" in result["metrics"]
        finally:
            eval_mod.stt_router.transcribe = orig_stt
            AudioQualityAnalyzer.analyze = orig_qa  # type: ignore
    finally:
        stg_mod.AIRouter = orig
        ai_mod.MonologueAIAnalyzer.evaluate = orig_eval
        ai_mod.MonologueAIAnalyzer.native_upgrade = orig_up

@pytest.mark.asyncio
async def test_monologue_durations_all(test_db):
    user = User(id="u_mono_3", display_name="Test3", locale="ja-JP")
    test_db.add(user)
    prof = LearnerProfile(user_id="u_mono_3", overall_level="N3", speaking_level="N3", confidence_score=0.5, level_confidence="medium", total_sessions_analyzed=0, total_turns_analyzed=0)
    test_db.add(prof)
    await test_db.commit()
    from app.domains.monologue.generation import speech_topic_generator as stg_mod
    orig = stg_mod.AIRouter
    class SuccessRouter:
        def __init__(self, db): pass
        async def generate(self, task, request, user_id):
            from unittest.mock import MagicMock
            m = MagicMock()
            # vary duration in response to match request
            import json, re
            # request contains duration; parse from messages
            dur = 60
            try:
                for msg in request.messages:
                    if "Duration:" in msg.content:
                        found = re.search(r"Duration:\s*(\d+)", msg.content)
                        if found:
                            dur = int(found.group(1))
            except Exception:
                pass
            m.text = json.dumps({"topic":f"トピック{dur}", "instruction":f"「トピック{dur}」について{dur}秒で話してください。", "constraints":["include_one_example"], "keywords":[], "outline":[], "difficulty":3, "expected_duration_sec":dur, "prep_duration_sec":15})
            m.provider="test"; m.model="test"
            return m
    stg_mod.AIRouter = SuccessRouter
    try:
        svc = MonologueService(test_db)
        for dur in [30,45,60,90,120,180,300]:
            ex = await svc.generate_exercise(user_id="u_mono_3", duration_sec=dur)
            assert ex.extra_metadata["speech_config"]["target_duration_sec"] == dur
    finally:
        stg_mod.AIRouter = orig
