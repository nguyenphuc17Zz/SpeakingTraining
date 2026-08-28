# Full-System Architecture Audit & Verification Report

## Executive Summary
This document provides a comprehensive architectural audit of the **Japanese Speaking AI Training OS (Hanasu AI)** spanning all 13 phases. The system is designed with a strict domain-driven architecture, deterministic pedagogical prioritization, real-time voice streaming pipelines, long-term learner memory, adaptive learning engines, RPG gamification loops, and an AI personal coach.

---

## 1. Domain Hierarchy & Source of Truth

```text
Raw User Interaction
  ├── Conversation (Audio / WebRTC / VAD)
  └── Shadowing (YouTube Audio / Transcripts)
            ↓
Assessment Subsystems
  ├── Conversation Intelligence (Deep Analysis / Corrections)
  └── Pronunciation Engine (Pitch Contour / Mora Timing / Phoneme Evaluation)
            ↓
Long-Term Learner State (Source of Truth)
  └── Learner Memory Domain (Error Memory, Strengths, Recurring Weaknesses)
            ↓
Training State (Curriculum & Practice)
  └── Learning Engine (LearningItems, Daily Plans, Exercises, Mastery)
            ↓
Derived Analytics & Observation
  └── Analytics Engine (Radar Metrics, Trend Detection, Snapshots, Weekly Reviews)
            ↓
Motivation & Habit Loop
  └── Gamification Engine (Immutable XP Ledger, Streaks, Quests, Badges, Boss Trials)
            ↓
Pedagogical Strategy & Explanation
  └── Personal AI Coach (Grounded Guidance, Practice Recommendations)
```

### Invariant Rules
1. **Analytics Engine never mutates Learning State**: Analytics solely computes aggregations, radar scores, and trends from historical sessions and exercise attempts.
2. **Gamification never alters Learning Difficulty**: XP rewards and streaks are awarded from verified learning events (`xp_transactions` ledger); they never artificially bump or lower learning item mastery.
3. **AI Coach delegates Practice to Learning Engine**: When a learner clicks *"Practice Now"* in AI Coach, it routes directly into the standard Learning Engine exercise pipeline.
4. **All AI Invocations Route through AI Router**: No subsystem calls raw LLM SDKs directly; all requests leverage `AIRouter` with automatic provider fallback (`Gemini` ➔ `Groq`), task tiers (`FAST`, `BALANCED`, `DEEP`), and token budgeting (`PromptBudgetGuard`).

---

## 2. Subsystem Map & Dependencies

| Subsystem | Primary Responsibilities | Dependencies |
|---|---|---|
| **AI Router (`domains/ai`)** | Multi-provider orchestration, fallbacks, token budget guard, deduplication | Google Gemini, Groq, OpenRouter |
| **Speech (`domains/speech`)** | STT transcription, Faster-Whisper GPU/CPU model management, LRU caching | `ctranslate2`, `faster_whisper` |
| **Audio Platform (`domains/audio`)** | VOICEVOX TTS synthesis, audio normalization, in-memory TTS cache | VOICEVOX Engine |
| **Conversation (`domains/conversation`)** | Live session lifecycle, turns, transcripts, latency metrics | `domains/speech`, `domains/ai`, `domains/audio` |
| **Intelligence (`domains/conversation_intelligence`)** | Background linguistic analysis, grammar corrections, naturalness | `domains/ai`, `domains/conversation` |
| **Learner Memory (`domains/learner_memory`)** | Persistent error memory, mastery scoring, recurring weaknesses | `domains/conversation_intelligence` |
| **Learning Engine (`domains/learning`)** | Daily plan generator, exercises, spaced repetition, mastery updates | `domains/learner_memory`, `domains/ai` |
| **Shadowing (`domains/shadowing`)** | YouTube audio extraction, sentence segmentation, shadowing drills | `yt-dlp`, `faster_whisper`, `domains/audio` |
| **Pronunciation (`domains/pronunciation`)** | Acoustic pitch analysis, mora duration assessment, phoneme scoring | `librosa`, `domains/speech` |
| **Gamification (`domains/gamification`)** | Immutable XP ledger, level curves, quests, achievements, boss battles | `domains/learning`, `domains/conversation` |
| **Analytics (`domains/analytics`)** | Radar metrics, weekly reviews, trend analysis, snapshot generator | `domains/conversation`, `domains/learning`, `domains/gamification` |
| **AI Coach (`domains/analytics/coach`)** | Grounded conversation coach, diagnostic insights, learning referrals | `domains/learner_memory`, `domains/learning`, `domains/ai` |

---

## 3. Background Workers Lifecycle

All 7 background workers implement standard async queues with graceful startup/shutdown and stale-job recovery:

1. **`AnalysisWorker`**: Background turn & session linguistic analysis.
2. **`PronunciationWorker`**: Deep acoustic pitch & mora alignment worker.
3. **`ShadowingImportWorker`**: YouTube audio download, Whisper transcription & sentence segmenter.
4. **`LearnerMemoryWorker`**: Learning signal extraction and memory consolidation.
5. **`LearningWorker`**: Exercise evaluation and mastery delta updates.
6. **`GameWorker`**: Learning event processing, XP ledger emission, and quest progress.
7. **`AnalyticsWorker`**: Session analytics record computation and snapshot updates.

---

## 4. Hardware Acceleration & Resilience

- **NVIDIA GPU / CUDA**: Faster-Whisper auto-detects CUDA hardware (`device="cuda"`, `compute_type="float16"`), falling back to multi-threaded CPU (`int8`) seamlessly.
- **VRAM LRU Eviction**: `WhisperModelManager` caps loaded models at 2, automatically freeing VRAM and invoking garbage collection & CUDA cache flushing on model switches.
- **Redis Graceful Fallback**: If Redis is offline, the API operates in high-performance in-memory queue & cache mode with zero downtime.
- **SQLite / PostgreSQL Portability**: Async session pooling for production PostgreSQL (`pool_size=10, max_overflow=20`), with automatic WAL pragmas for local SQLite.
