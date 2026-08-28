import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.contracts import AIUsage
from app.domains.ai.service import AIUsageService
from app.domains.users.service import UserService


@pytest.mark.asyncio
async def test_ai_usage_service_recording(db_session: AsyncSession):
    user_service = UserService(db_session)
    user = await user_service.get_or_create_default_user()

    service = AIUsageService(db_session)

    # Record request 1
    await service.record_usage(
        user_id=user.id,
        request_id="req-001",
        provider="gemini",
        model="gemini-1.5-flash",
        task="conversation",
        latency_ms=350,
        usage=AIUsage(input_tokens=100, output_tokens=50, total_tokens=150),
        success=True,
    )

    # Record request 2
    await service.record_usage(
        user_id=user.id,
        request_id="req-002",
        provider="groq",
        model="llama-3.3-70b-versatile",
        task="grammar_correction",
        latency_ms=150,
        usage=AIUsage(input_tokens=80, output_tokens=40, total_tokens=120),
        success=True,
        fallback_occurred=True,
        attempts_count=2,
    )

    summary = await service.get_usage_summary(user_id=user.id)

    assert summary.total_requests == 2
    assert summary.successful_requests == 2
    assert summary.failed_requests == 0
    assert summary.total_input_tokens == 180
    assert summary.total_output_tokens == 90
    assert summary.total_tokens == 270
    assert summary.avg_latency_ms == 250.0
    assert len(summary.recent_records) == 2
