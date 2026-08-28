from datetime import datetime, timezone
from typing import Any
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.gamification.domain.balance_config import BALANCE_CONFIG
from app.domains.gamification.domain.contracts import GameEventSource, GameEventType, XPCategory
from app.domains.gamification.domain.game_event import GameEvent
from app.domains.gamification.models import BossAttempt, BossDefinition, GameProfile
from app.domains.gamification.schemas import BossAttemptResultDTO, BossDTO, BossStartResponseDTO
from app.domains.learning.models import Exercise, ExerciseAttempt
from app.shared.errors.exceptions import NotFoundException, ValidationException


class BossService:
    """
    Manages Japanese Speaking Boss Battles — high-stakes conversational challenges.
    Reuses existing Conversation and Exercise evaluation engines rather than creating duplicate AI systems.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_bosses_dto(self, user_id: str) -> list[BossDTO]:
        """Returns all boss challenges with unlock status and user personal bests."""
        # Fetch profile for level
        prof_stmt = select(GameProfile).where(GameProfile.user_id == user_id)
        prof_res = await self.db.execute(prof_stmt)
        profile = prof_res.scalar_one_or_none()
        current_level = profile.level if profile else 1

        # Fetch boss definitions
        defs_stmt = select(BossDefinition).order_by(BossDefinition.required_level.asc())
        defs_res = await self.db.execute(defs_stmt)
        boss_defs = list(defs_res.scalars().all())

        dtos = []
        for bd in boss_defs:
            is_unlocked = current_level >= bd.required_level

            # Fetch attempts
            att_stmt = (
                select(BossAttempt)
                .where(BossAttempt.user_id == user_id, BossAttempt.boss_id == bd.id)
                .order_by(desc(BossAttempt.score))
            )
            att_res = await self.db.execute(att_stmt)
            attempts = list(att_res.scalars().all())

            best_score = attempts[0].score if attempts else None
            cleared = any(a.passed for a in attempts)
            total_attempts = len(attempts)

            dtos.append(
                BossDTO(
                    id=bd.id,
                    key=bd.key,
                    name=bd.name,
                    subtitle=bd.subtitle,
                    description=bd.description,
                    difficulty=bd.difficulty,
                    required_level=bd.required_level,
                    is_unlocked=is_unlocked,
                    pass_score_threshold=bd.pass_score_threshold,
                    xp_reward=bd.xp_reward,
                    title_reward=bd.title_reward,
                    objectives=bd.objectives_json or [],
                    personal_best_score=best_score,
                    cleared=cleared,
                    total_attempts=total_attempts,
                )
            )
        return dtos

    async def start_boss_battle(self, user_id: str, boss_id: str) -> BossStartResponseDTO:
        """
        Instantiates a specialized Exercise challenge tied to this Boss Definition.
        """
        boss_stmt = select(BossDefinition).where(BossDefinition.id == boss_id)
        boss_res = await self.db.execute(boss_stmt)
        boss = boss_res.scalar_one_or_none()
        if not boss:
            raise NotFoundException(f"Boss challenge '{boss_id}' not found.")

        # Check level requirement
        prof_stmt = select(GameProfile).where(GameProfile.user_id == user_id)
        prof_res = await self.db.execute(prof_stmt)
        profile = prof_res.scalar_one_or_none()
        current_level = profile.level if profile else 1

        if current_level < boss.required_level:
            raise ValidationException(
                f"Boss requires RPG Level {boss.required_level}. Current Level: {current_level}."
            )

        # Create linked Exercise record
        exercise = Exercise(
            user_id=user_id,
            exercise_type="boss_battle",
            status="in_progress",
            title=f"🔥 BOSS: {boss.name}",
            objective=boss.description,
            scenario=boss.scenario_template or f"High-stakes conversation with {boss.name}.",
            instructions="Maintain natural Japanese speaking fluency and achieve the target communicative goals.",
            difficulty=boss.difficulty,
            estimated_minutes=10,
            constraints=boss.objectives_json or [],
            extra_metadata={
                "boss_id": boss.id,
                "boss_key": boss.key,
                "persona_key": boss.persona_key,
                "pass_score_threshold": boss.pass_score_threshold,
            },
        )
        self.db.add(exercise)
        await self.db.commit()
        await self.db.refresh(exercise)

        logger.info(f"[BossService] Started Boss challenge '{boss.name}' for user {user_id}")

        return BossStartResponseDTO(
            boss_id=boss.id,
            boss_name=boss.name,
            exercise_id=exercise.id,
            persona_key=boss.persona_key,
            instructions=exercise.instructions,
            objectives=boss.objectives_json or [],
        )

    async def submit_boss_result(
        self,
        user_id: str,
        boss_id: str,
        exercise_attempt_id: str,
    ) -> BossAttemptResultDTO:
        """
        Evaluates boss attempt from completed ExerciseAttempt, determines pass/fail, and calculates rewards.
        """
        boss_stmt = select(BossDefinition).where(BossDefinition.id == boss_id)
        boss_res = await self.db.execute(boss_stmt)
        boss = boss_res.scalar_one_or_none()
        if not boss:
            raise NotFoundException(f"Boss challenge '{boss_id}' not found.")

        # Fetch ExerciseAttempt
        att_stmt = select(ExerciseAttempt).where(
            ExerciseAttempt.id == exercise_attempt_id,
            ExerciseAttempt.user_id == user_id,
        )
        att_res = await self.db.execute(att_stmt)
        exercise_att = att_res.scalar_one_or_none()
        if not exercise_att:
            raise NotFoundException(f"Exercise attempt '{exercise_attempt_id}' not found.")

        score = float(exercise_att.score or 0.0)
        passed = score >= boss.pass_score_threshold

        # Anti-farming: Check if already cleared previously
        prev_clear_stmt = select(BossAttempt).where(
            BossAttempt.user_id == user_id,
            BossAttempt.boss_id == boss.id,
            BossAttempt.passed == True,
        )
        prev_clear_res = await self.db.execute(prev_clear_stmt)
        had_cleared_before = len(list(prev_clear_res.scalars().all())) > 0

        xp_awarded = 0
        title_awarded = None

        if passed:
            if not had_cleared_before:
                # First clear: full reward
                xp_awarded = boss.xp_reward
                title_awarded = boss.title_reward
            else:
                # Repeat clear: reduced reward
                xp_awarded = int(boss.xp_reward * 0.30)

        # Record BossAttempt
        boss_att = BossAttempt(
            user_id=user_id,
            boss_id=boss.id,
            exercise_attempt_id=exercise_att.id,
            session_id=exercise_att.session_id,
            score=score,
            passed=passed,
            xp_awarded=xp_awarded,
            metrics_json=exercise_att.metrics_json or {},
            feedback=exercise_att.feedback,
            attempted_at=datetime.now(timezone.utc),
        )
        self.db.add(boss_att)
        await self.db.commit()
        await self.db.refresh(boss_att)

        weak_points = []
        if not passed:
            weak_points.append("Fluency under pressure")
            weak_points.append("Target grammar accuracy")

        logger.info(
            f"[BossService] User {user_id} finished Boss '{boss.name}' (Score: {score}, Passed: {passed}, XP: {xp_awarded})"
        )

        return BossAttemptResultDTO(
            attempt_id=boss_att.id,
            boss_id=boss.id,
            score=score,
            passed=passed,
            xp_awarded=xp_awarded,
            title_awarded=title_awarded,
            metrics=exercise_att.metrics_json or {},
            feedback=exercise_att.feedback,
            weak_points=weak_points,
            recommended_training="Review key grammar patterns and try an interactive roleplay drill.",
        )
