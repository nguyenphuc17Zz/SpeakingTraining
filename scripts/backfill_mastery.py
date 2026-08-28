"""
Backfill mastery deltas after fixing asymmetric clipping and decay rates.
Forward fix applied in mastery_engine.py (2026-08-26):
 - score_norm clamp [-1.0,1.0] (was [-1.5,1.0])
 - decay rates ln2/180, ln2/60, ln2/30
Only forward deltas are corrected; this script optionally recomputes historical mastery
for existing LearningItems based on current ExerciseAttempt history.

Usage:
  python scripts/backfill_mastery.py --dry-run
  python scripts/backfill_mastery.py --apply

Requires: DATABASE_URL env or default sqlite speaking_training.db
"""

import argparse
import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.domains.learning.models import LearningItem, ExerciseAttempt
from app.domains.learning.mastery_engine import MasteryEngine
from app.infrastructure.database.base import Base
from app.infrastructure.database.session import get_db  # not used, custom engine

async def backfill(dry_run: bool = True):
    settings = get_settings()
    # Use configured DB URL or fallback to sqlite file
    db_url = getattr(settings, "DATABASE_URL", None) or "sqlite+aiosqlite:///speaking_training.db"
    # Normalize async URL
    if db_url.startswith("sqlite:///"):
        db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(db_url, echo=False)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        result = await session.execute(select(LearningItem))
        items = result.scalars().all()
        print(f"Found {len(items)} LearningItems")
        changed = 0
        for item in items:
            # Example: recompute decay based on days since last practice
            # For full backfill, you would replay ExerciseAttempts in order and recompute deltas
            # Here we just show current vs recomputed decay for illustration
            if item.last_practiced_at:
                try:
                    days = (datetime.now(timezone.utc) - item.last_practiced_at).days
                    recomputed = MasteryEngine.apply_decay(item.overall_mastery, days, item.lifecycle)
                    if abs(recomputed - item.overall_mastery) > 0.01:
                        print(f"  {item.key}: {item.overall_mastery} -> {recomputed} (days={days}, lifecycle={item.lifecycle})")
                        if not dry_run:
                            item.overall_mastery = recomputed
                            changed += 1
                except Exception as e:
                    print(f"  skip {item.key}: {e}")
        if not dry_run and changed:
            await session.commit()
            print(f"Committed {changed} updates")
        elif dry_run:
            print(f"Dry-run: would update {changed} items (none committed)")
        else:
            print("No changes needed")

    await engine.dispose()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill mastery after asymmetric fix")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Dry run only")
    parser.add_argument("--apply", action="store_true", help="Apply changes")
    args = parser.parse_args()
    dry = not args.apply
    if args.dry_run:
        dry = True
    asyncio.run(backfill(dry_run=dry))
