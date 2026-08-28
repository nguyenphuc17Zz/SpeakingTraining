# Release Checklist & Production Verification

Use this checklist before cutting a release or starting long-term continuous training.

---

## Production Release Checklist

### 1. Automated Tests & Code Integrity
- [x] **Pytest Suite**: All 159 unit, integration, and contract tests pass (`python -m pytest tests/`).
- [x] **Next.js Web Build**: `npm run build` succeeds with 25/25 routes statically/dynamically compiled and 0 TypeScript errors.
- [x] **Data Integrity Audit**: `python scripts/verify_data_integrity.py` verifies zero orphaned turns, memory mismatches, or XP discrepancies.
- [x] **Preflight Verification**: `python scripts/preflight.py` returns status `[STATUS: PRODUCTION READY]`.

### 2. Environment & Secrets
- [x] **Encryption Key**: 32-byte URL-safe base64 `ENCRYPTION_KEY` configured in `.env`.
- [x] **Zero Plaintext Secrets**: Verified that no raw API credentials appear in logs or client-side responses.
- [x] **CORS Origins**: Allowed origins restricted to production frontend domains.

### 3. Database & Storage
- [x] **PostgreSQL Connection Pool**: Async pool configured with `pool_pre_ping=True` and `pool_recycle=3600`.
- [x] **SQLite WAL Mode**: PRAGMA listeners active for local zero-lock development.
- [x] **Temp Storage Cleanup**: `python scripts/cleanup_media.py --apply` clears stale temporary audio recordings.

### 4. Hardware & Speech Engines
- [x] **Faster-Whisper CUDA Auto-Detection**: GPU accelerated inference active (`device="cuda"`), with CPU fallback.
- [x] **LRU Whisper Eviction**: Loaded models capped at 2 to prevent VRAM exhaustion.
- [x] **VOICEVOX Engine**: Endpoint reachable at `http://127.0.0.1:50021` with in-memory caching (500 items, 2h TTL).

### 5. Background Workers & Resiliency
- [x] **Stale Job Recovery**: All workers automatically rescue orphaned `processing` jobs on startup.
- [x] **Redis Graceful Fallback**: In-memory queue operates transparently if Redis is unavailable.
- [x] **Centralized Upload Caps**: 10 MB audio payload and 4,000-character prompt limits enforced.
