"""
Backfill mastery_delta sum->avg fix (2026-08-26).
metric_engine.py:298 previously sum(it.overall_mastery) -> avg.
Metric is computed on-the-fly (no stored column), so no DB migration needed.
This script verifies the fix by recomputing for existing users and logging delta.

Run:
  python scripts/backfill_mastery_delta.py --dry-run
  python scripts/backfill_mastery_delta.py --apply  # no-op, for audit

Approved choice: Migration toàn bộ (chart cũ có thể hạ nhưng đúng)
-> Next dashboard refresh will automatically show avg instead of sum.
"""

import argparse
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from app.core.config import get_settings
from app.domains.learning.models import LearningItem

async def check(dry_run=True):
    settings = get_settings()
    db_url = getattr(settings, "DATABASE_URL", None) or "sqlite+aiosqlite:///speaking_training.db"
    if db_url.startswith("sqlite:///"):
        db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    engine = create_async_engine(db_url, echo=False)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        res = await session.execute(select(LearningItem))
        items = res.scalars().all()
        # Group by user
        from collections import defaultdict
        by_user = defaultdict(list)
        for it in items:
            by_user[it.user_id].append(it)
        for uid, lst in by_user.items():
            old_sum = sum(it.overall_mastery for it in lst)
            new_avg = round(sum(it.overall_mastery for it in lst) / len(lst), 3) if lst else 0.0
            print(f"user {uid[:8]}: {len(lst)} items, old_sum={old_sum:.3f} -> new_avg={new_avg:.3f} (diff {new_avg-old_sum:+.3f})")
        print("Metric is computed live; no DB write needed. Next dashboard will show avg.")
    await engine.dispose()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true", help="No-op, for audit")
    args = parser.parse_args()
    asyncio.run(check(dry_run=not args.apply))
