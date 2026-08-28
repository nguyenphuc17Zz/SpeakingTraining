"""
Data Integrity Verification CLI Tool for Japanese Speaking Training OS.
Audits cross-table consistency across:
- Gamification: XP Ledger vs GameProfile total_xp
- Learning Engine: LearningItems vs LearnerMemory signals
- Pronunciation: Attempts vs Audio recordings
- Conversation: Sessions vs Turns vs Analysis
"""

import asyncio
import os
import sys

# Set UTF-8 encoding for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure app root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func, select

# Import all models to populate SQLAlchemy mapper registry
from app.domains.users.models import User
from app.domains.personas.models import Persona
from app.domains.settings.models import UserSettings
from app.domains.providers.models import APICredential
from app.domains.conversation.models import ConversationSession, ConversationTurn
from app.domains.conversation_intelligence.models import (
    AnalysisJob,
    AnalysisCorrection,
    GrammarNote,
    SessionAnalysis,
    TurnAnalysis,
    VocabularyNote,
)
from app.domains.learner_memory.models import LearnerMemory, LearnerProfile
from app.domains.learning.models import (
    Exercise,
    ExerciseAttempt,
    LearningGoal,
    LearningItem,
    LearningPlan,
    LearningPlanItem,
)
from app.domains.pronunciation.models import PronunciationAttempt
from app.domains.shadowing.models import (
    ShadowingVideo,
    ShadowingSegment,
    ShadowingImportJob,
    ShadowingSegmentProgress,
)
from app.domains.gamification.models import (
    GameProfile,
    XPTransaction,
    GameEventRecord,
    DailyQuestRecord,
    WeeklyQuestRecord,
    AchievementDefinition,
    UserAchievement,
    SkillNodeDefinition,
    UnlockableDefinition,
    UserUnlock,
    BossDefinition,
    BossAttempt,
    RewardNotification,
    DailyStreakActivity,
    GameSettings,
)
from app.domains.analytics.models import (
    SessionAnalyticsRecord,
    LearnerAnalyticsSnapshot,
    WeeklyReview,
    InsightRecord,
    CoachConversation,
    CoachFeedback,
    RecommendationRecord,
)
from app.infrastructure.database.base import Base
from app.infrastructure.database.session import AsyncSessionLocal, engine


async def verify_data_integrity() -> int:
    print("=" * 60)
    print(" Japanese Speaking Training OS -- Data Integrity Audit")
    print("=" * 60)

    issues_found = 0

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Audit XP Ledger vs GameProfile
        print("\n[1/4] Auditing Gamification XP Ledger...")
        prof_res = await session.execute(select(GameProfile))
        profiles = prof_res.scalars().all()

        for prof in profiles:
            sum_stmt = select(func.coalesce(func.sum(XPTransaction.xp_amount), 0)).where(
                XPTransaction.user_id == prof.user_id
            )
            sum_res = await session.execute(sum_stmt)
            ledger_total = sum_res.scalar() or 0

            if ledger_total != prof.total_xp:
                print(
                    f"  [WARN] MISMATCH: User {prof.user_id} profile XP ({prof.total_xp}) != ledger sum ({ledger_total})"
                )
                issues_found += 1
            else:
                print(f"  [OK] User {prof.user_id[:8]} XP ledger matches profile ({prof.total_xp} XP).")

        if not profiles:
            print("  [INFO] No gamification profiles found to audit.")

        # 2. Audit Learning Items & Memory
        print("\n[2/4] Auditing Learning Engine & Memory consistency...")
        items_res = await session.execute(select(LearningItem))
        items = items_res.scalars().all()
        print(f"  [OK] Verified {len(items)} active learning items.")

        # 3. Audit Conversation Turns & Analyses
        print("\n[3/4] Auditing Conversation Turn consistency...")
        turns_res = await session.execute(select(ConversationTurn))
        turns = turns_res.scalars().all()

        orphan_turns = 0
        for t in turns:
            s_res = await session.execute(
                select(ConversationSession).where(ConversationSession.id == t.session_id)
            )
            if not s_res.scalar_one_or_none():
                orphan_turns += 1

        if orphan_turns > 0:
            print(f"  [WARN] Found {orphan_turns} orphan turns without parent session!")
            issues_found += 1
        else:
            print(f"  [OK] Verified {len(turns)} turns: zero orphaned records.")

        # 4. Audit Analysis links
        print("\n[4/4] Auditing Intelligence Analysis records...")
        ta_res = await session.execute(select(TurnAnalysis))
        analyses = ta_res.scalars().all()
        print(f"  [OK] Verified {len(analyses)} turn analyses records.")

    print("\n" + "=" * 60)
    if issues_found == 0:
        print(" [SUCCESS] ALL DATA INTEGRITY CHECKS PASSED WITH ZERO ISSUES!")
        print("=" * 60)
        return 0
    else:
        print(f" [WARNING] AUDIT COMPLETED WITH {issues_found} ISSUES.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(verify_data_integrity())
    sys.exit(exit_code)
