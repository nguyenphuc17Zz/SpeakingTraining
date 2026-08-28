import pytest
from app.infrastructure.redis.client import RedisManager
from app.domains.learning.queue import LearningJobQueue
from app.domains.learner_memory.queue import LearnerMemoryJobQueue


@pytest.mark.asyncio
async def test_redis_manager_client_property():
    mgr = RedisManager(url="redis://localhost:6379/0")
    # Verify .client property exists and returns redis client
    client = mgr.client
    assert client is not None
    await mgr.close()


@pytest.mark.asyncio
async def test_learning_job_queue_memory_fallback():
    queue = LearningJobQueue()
    job_data = {"task_type": "DAILY_PLAN_GENERATION", "user_id": "test-user-123"}
    await queue.enqueue(job_data)
    dequeued = await queue.dequeue(timeout_seconds=0.5)
    assert dequeued is not None
    assert dequeued.get("task_type") == "DAILY_PLAN_GENERATION"
    assert dequeued.get("user_id") == "test-user-123"


@pytest.mark.asyncio
async def test_learner_memory_job_queue_memory_fallback():
    queue = LearnerMemoryJobQueue()
    job_data = {"session_id": "test-session-456", "user_id": "test-user-123"}
    await queue.enqueue(job_data)
    dequeued = await queue.dequeue(timeout_seconds=0.5)
    assert dequeued is not None
    assert dequeued.get("session_id") == "test-session-456"
    assert dequeued.get("user_id") == "test-user-123"
