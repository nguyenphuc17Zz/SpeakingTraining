from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings
from app.domains.ai.models import AIUsageRecord  # noqa: F401
from app.domains.analytics.models import (  # noqa: F401
    CoachConversation,
    CoachFeedback,
    InsightRecord,
    LearnerAnalyticsSnapshot,
    RecommendationRecord,
    SessionAnalyticsRecord,
    WeeklyReview,
)
from app.domains.audio.models import AudioPresetModel, VoiceProfileModel  # noqa: F401
from app.domains.conversation.models import ConversationSession, ConversationTurn  # noqa: F401
from app.domains.conversation_intelligence.models import (  # noqa: F401
    AnalysisCorrection,
    AnalysisJob,
    AnalysisUserFeedback,
    GrammarNote,
    SessionAnalysis,
    TurnAnalysis,
    VocabularyNote,
)
from app.domains.gamification.models import (  # noqa: F401
    AchievementDefinition,
    BossAttempt,
    BossDefinition,
    DailyQuestRecord,
    DailyStreakActivity,
    GameEventRecord,
    GameProfile,
    GameSettings,
    RewardNotification,
    SkillNodeDefinition,
    UnlockableDefinition,
    UserAchievement,
    UserUnlock,
    WeeklyQuestRecord,
    XPTransaction,
)
from app.domains.gamification.seeds import GamificationSeeder
from app.domains.learner_memory.models import (  # noqa: F401
    LearnerMemory,
    LearnerProfile,
    MemoryEvidence,
    MemoryFeedback,
)
from app.domains.learning.models import (  # noqa: F401
    Exercise,
    ExerciseAttempt,
    ExerciseTemplate,
    LearningGoal,
    LearningItem,
    LearningPlan,
    LearningPlanItem,
)
from app.domains.personas.models import Persona, UserPersonaPreference  # noqa: F401
from app.domains.personas.service import PersonaService
from app.domains.pronunciation.models import PronunciationAttempt, PronunciationPracticeTarget  # noqa: F401
from app.domains.providers.models import APICredential  # noqa: F401
from app.domains.settings.models import UserSettings  # noqa: F401
from app.domains.settings.service import SettingsService
from app.domains.shadowing.models import (  # noqa: F401
    ShadowingBookmark,
    ShadowingImportJob,
    ShadowingSegment,
    ShadowingSegmentProgress,
    ShadowingTranscript,
    ShadowingVideo,
    ShadowingVideoProgress,
)
from app.domains.users.models import User  # noqa: F401
from app.domains.users.service import UserService
from app.infrastructure.database.base import Base
from app.infrastructure.database.session import get_db
from app.main import create_app

# Test in-memory database URL
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    future=True,
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    settings = get_settings()
    settings.APP_ENV = "test"
    settings.DEBUG = False
    return settings


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSessionLocal() as session:
        # Seed personas and default user
        persona_service = PersonaService(session)
        await persona_service.seed_system_personas()
        user_service = UserService(session)
        user = await user_service.get_or_create_default_user()
        settings_service = SettingsService(session)
        await settings_service.get_or_create_settings(user.id)
        await GamificationSeeder.seed_defaults(session)

        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
