import pytest
from app.domains.shadowing.service import ShadowingService
from app.domains.shadowing.models import ShadowingVideo, ShadowingSegment
from app.domains.users.models import User
import base64
import numpy as np
import io
import wave

def create_dummy_wav() -> str:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        # 1.5 seconds of 440Hz sine wave tone
        t = np.linspace(0, 1.5, int(16000 * 1.5), endpoint=False)
        samples = (np.sin(2 * np.pi * 440 * t) * 10000).astype(np.int16)
        wf.writeframes(samples.tobytes())
    return base64.b64encode(buf.getvalue()).decode("utf-8")

@pytest.mark.asyncio
async def test_multi_turn_shadowing_consecutive_attempts(db_session):
    # Setup test user and video segment
    user = User(id="test-user-multi", display_name="Multi Learner")
    video = ShadowingVideo(
        id="vid-multi-1",
        video_id="abc1234",
        url="https://youtube.com/watch?v=abc1234",
        canonical_url="https://youtube.com/watch?v=abc1234",
        title="Test Multi",
        channel_name="Test Channel",
        import_status="ready",
    )
    from app.domains.shadowing.models import ShadowingTranscript
    transcript = ShadowingTranscript(
        id="tr-multi-1",
        video_id="vid-multi-1",
        source="whisper",
    )
    segment = ShadowingSegment(
        id="seg-multi-1",
        video_id="vid-multi-1",
        transcript_id="tr-multi-1",
        start_time=1.0,
        end_time=4.0,
        text="みなさんこんにちは",
        normalized_text="みなさんこんにちは",
        sequence=0,
    )
    db_session.add_all([user, video, transcript, segment])
    await db_session.commit()

    service = ShadowingService(db_session)
    dummy_audio = create_dummy_wav()

    # Turn 1
    start_1 = await service.start_segment_practice(
        segment_id="seg-multi-1",
        user_id="test-user-multi",
        shadowing_mode="shadow",
    )
    assert start_1.exercise_id is not None
    assert start_1.attempt_id is not None

    complete_1 = await service.complete_segment_practice(
        exercise_id=start_1.exercise_id,
        attempt_id=start_1.attempt_id,
        audio_base64=dummy_audio,
        user_id="test-user-multi",
        client_transcript="みなさんこんにちは",
    )
    assert complete_1.score > 0

    # Turn 2 (Consecutive attempt on same segment)
    start_2 = await service.start_segment_practice(
        segment_id="seg-multi-1",
        user_id="test-user-multi",
        shadowing_mode="shadow",
    )
    assert start_2.exercise_id is not None
    assert start_2.attempt_id is not None

    complete_2 = await service.complete_segment_practice(
        exercise_id=start_2.exercise_id,
        attempt_id=start_2.attempt_id,
        audio_base64=dummy_audio,
        user_id="test-user-multi",
        client_transcript="みなさんこんにちは",
    )
    assert complete_2.score > 0
