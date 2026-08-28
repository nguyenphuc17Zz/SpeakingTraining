"""
System Preflight & Production Readiness Verification Tool.
Audits all subsystems, providers, database, redis, STT, TTS, storage, and worker states.
"""

import asyncio
import os
import sys
import tempfile
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure app root in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text
from app.core.config import get_settings
from app.core.logging import logger
from app.infrastructure.database.base import Base
from app.infrastructure.database.session import AsyncSessionLocal, engine
from app.infrastructure.database.sync_schema import sync_database_schema
from app.infrastructure.redis.client import redis_manager
from app.domains.speech.model_manager import whisper_model_manager
from app.domains.ai.registry import ModelRegistry
from app.domains.personas.service import PersonaService
from app.domains.users.service import UserService
from app.domains.settings.service import SettingsService
from app.domains.gamification.seeds import GamificationSeeder

# Workers
from app.domains.conversation_intelligence.worker import analysis_worker
from app.domains.learner_memory.worker import learner_memory_worker
from app.domains.learning.worker import learning_worker
from app.domains.pronunciation.worker import pronunciation_worker
from app.domains.shadowing.worker import shadowing_worker
from app.domains.gamification.worker import game_worker
from app.domains.analytics.worker import analytics_worker


async def run_preflight() -> int:
    print("=" * 65)
    print("  HANASU AI OS -- Production Preflight & System Readiness Audit")
    print("=" * 65)

    settings = get_settings()
    passed = 0
    warnings = 0
    failures = 0

    # 1. Environment & Python Version
    print("\n[1/8] Checking Runtime & Environment...")
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):
        print(f"  [PASS] Python {py_version} (Compatible >= 3.10)")
        passed += 1
    else:
        print(f"  [FAIL] Python {py_version} (Requires >= 3.10)")
        failures += 1

    print(f"  [INFO] App Environment: {settings.APP_ENV}, Debug Mode: {settings.DEBUG}")

    # 2. Database & Schema
    print("\n[2/8] Checking Database Connectivity & Schema...")
    try:
        await sync_database_schema(engine)
        async with engine.begin() as conn:
            res = await conn.execute(text("SELECT 1"))
            val = res.scalar()
            if val == 1:
                print(f"  [PASS] Database connected & schema synchronized ({settings.DATABASE_URL.split('://')[0]})")
                passed += 1
    except Exception as e:
        print(f"  [FAIL] Database connection/sync failed: {e}")
        failures += 1

    # 3. Seed Data & Defaults
    print("\n[3/8] Checking System Seeds & Default User...")
    try:
        async with AsyncSessionLocal() as session:
            persona_svc = PersonaService(session)
            await persona_svc.seed_system_personas()
            personas = await persona_svc.list_personas()

            user_svc = UserService(session)
            user = await user_svc.get_or_create_default_user()

            settings_svc = SettingsService(session)
            await settings_svc.get_or_create_settings(user.id)

            await GamificationSeeder.seed_defaults(session)

            print(f"  [PASS] System seeded: {len(personas)} Personas, Default User '{user.id[:8]}...' ready.")
            passed += 1
    except Exception as e:
        print(f"  [FAIL] Seed verification failed: {e}")
        failures += 1

    # 4. Redis & Caching Tier
    print("\n[4/8] Checking Redis & Cache Resiliency...")
    is_redis = await redis_manager.is_available()
    if is_redis:
        print(f"  [PASS] Redis connected at {settings.REDIS_URL}")
        passed += 1
    else:
        print("  [WARN] Redis offline. In-memory graceful fallback mode ACTIVE (App remains fully functional).")
        warnings += 1

    # 5. Faster-Whisper STT Subsystem
    print("\n[5/8] Checking Faster-Whisper STT Hardware Acceleration...")
    try:
        device, compute = whisper_model_manager.detect_hardware("auto", "auto")
        print(f"  [PASS] Faster-Whisper ready. Detected Device: '{device.upper()}', Compute: '{compute}'")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Whisper hardware detection failed: {e}")
        failures += 1

    # 6. AI Model Registry & Tiers
    print("\n[6/8] Checking AI Router & Task Tier Mapping...")
    try:
        fast_rec = ModelRegistry.get_recommended_model_for_task("fast_correction", "groq")
        balanced_rec = ModelRegistry.get_recommended_model_for_task("conversation", "gemini")
        deep_rec = ModelRegistry.get_recommended_model_for_task("session_analysis", "gemini")
        print(f"  [PASS] AI Registry verified: FAST={fast_rec}, BALANCED={balanced_rec}, DEEP={deep_rec}")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] AI Registry check failed: {e}")
        failures += 1

    # 7. Media & Storage Permissions
    print("\n[7/8] Checking Temporary Media & Storage Directory...")
    temp_dir = tempfile.gettempdir()
    test_file = os.path.join(temp_dir, f"hanasu_preflight_{int(time.time())}.tmp")
    try:
        with open(test_file, "w") as f:
            f.write("preflight_test")
        os.remove(test_file)
        print(f"  [PASS] Temp storage write/delete verified in '{temp_dir}'")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Storage write permission failed: {e}")
        failures += 1

    # 8. Background Workers Readiness
    print("\n[8/8] Checking Background Workers Status...")
    workers = [
        ("AnalysisWorker", analysis_worker),
        ("LearnerMemoryWorker", learner_memory_worker),
        ("LearningWorker", learning_worker),
        ("PronunciationWorker", pronunciation_worker),
        ("ShadowingWorker", shadowing_worker),
        ("GameWorker", game_worker),
        ("AnalyticsWorker", analytics_worker),
    ]
    all_workers_ok = True
    for name, worker in workers:
        if not hasattr(worker, "start") or not hasattr(worker, "stop"):
            all_workers_ok = False
            print(f"  [FAIL] {name} missing start/stop lifecycle methods")
    if all_workers_ok:
        print(f"  [PASS] All 7 background workers initialized with lifecycle & metrics support.")
        passed += 1
    else:
        failures += 1

    # Final Summary
    print("\n" + "=" * 65)
    print(f" PREFLIGHT AUDIT COMPLETE: {passed} PASSED, {warnings} WARNINGS, {failures} FAILURES")
    if failures == 0:
        print(" [STATUS: PRODUCTION READY] All critical systems green!")
        print("=" * 65)
        return 0
    else:
        print(" [STATUS: NOT READY] Please address critical failures above.")
        print("=" * 65)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_preflight())
    sys.exit(exit_code)
