# Technical Debt Register

This register classifies technical debt and deferred decisions with impact and future remediation paths.

---

## Technical Debt Classification

| ID | Domain | Issue Description | Impact | Priority | Status / Future Solution |
|---|---|---|---|---|---|
| **TD-01** | **Speech** | Faster-Whisper is loaded in-process rather than via a dedicated microservice. | Model weights share process RAM/VRAM with FastAPI. Managed via `WhisperModelManager` with LRU eviction (max 2 models). | **P2** (Medium) | Acceptable for personal/single-user OS. For multi-tenant cloud scale, extract to a Triton / Faster-Whisper gRPC microservice. |
| **TD-02** | **Audio** | VOICEVOX synthesis is synchronous REST HTTP per sentence. | High-concurrency TTS requests queue behind the single-threaded local engine. | **P2** (Medium) | Add streaming chunked synthesis and parallel worker pool for multi-sentence audio. |
| **TD-03** | **Shadowing** | YouTube video streams are played client-side via YouTube IFrame rather than cached raw video files. | Requires network access to YouTube servers during shadowing sessions. | **P3** (Low) | Intentional architecture decision: avoids storing gigabytes of copyrighted video files locally; only stores lightweight extracted audio segments for pitch comparison. |
| **TD-04** | **Database** | SQLite lacks native async concurrency for high-write bursts without WAL mode. | Handled via SQLite WAL pragmas and async PostgreSQL connection pooling. | **P3** (Low) | Resolved: `session.py` automatically configures WAL pragma for SQLite and full asyncpg pooling for PostgreSQL. |

---

## Technical Debt Summary
- **P0 Critical**: 0 items. (All critical data integrity, security, and lifecycle issues resolved in Phases 12 & 13).
- **P1 High**: 0 items.
- **P2 Medium**: 2 items (Documented above: in-process Whisper model scaling, VOICEVOX streaming).
- **P3 Low**: 2 items (YouTube IFrame playback, SQLite single-file development).
