# Japanese Speaking AI Training OS (日本語スピーキング・トレーニングOS)

An AI-first, domain-driven training platform for mastering Japanese speaking through real-time voice conversations, background linguistic intelligence, long-term learner memory & error intelligence, pronunciation acoustics, adaptive curriculum & learning engine, and gamification.

---

## Roadmap & Implementation Phases

### ✅ Phase 1 — Foundation Architecture
- **Backend API (`apps/api`)**: Python, FastAPI, SQLAlchemy 2.0 (async/sync), Alembic, Pydantic v2, AES/Fernet encryption for provider keys, domain-driven architecture.
- **Frontend Web (`apps/web`)**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, Lucide icons, Framer Motion, Japanese/Anime aesthetic.
- **Shared Contracts (`packages/ai-contracts`)**: Typed model metadata and capability contracts.
- **Security**: AES-256/Fernet secret encryption, zero plaintext key logging, masked transmission (`sk-••••••••1234`).
- **Infrastructure (`infrastructure/docker`)**: Docker Compose for PostgreSQL 16 & Redis 7.

### ✅ Phase 2 — AI Provider & Model System
- **Unified AI Contracts**: Normalized `AIRequest`, `AIResponse`, and streaming `AIStreamEvent`.
- **Multi-Provider Adapters**: Google Gemini (`v1beta` REST/SSE), Groq LPU (Ultra-fast inference), and OpenRouter.
- **Intelligent AI Router**: Dynamic provider matching, automatic retry & failover cascade (`Auto` mode: Gemini ➔ Groq fallback), circuit breaker health monitoring.
- **Token & Latency Usage Tracking**: `ai_usage_records` persistent store for fine-grained token and latency telemetry.
- **Interactive AI Playground**: Real-time diagnostic playground and settings management UI.

### ✅ Phase 3 — Voice Conversation MVP
- **Real-Time Voice Pipeline**:
  ```text
  Browser Mic (Web Audio API) ➔ Utterance VAD ➔ Faster-Whisper STT ➔ Context Engine ➔ AI Router ➔ VOICEVOX TTS ➔ AI Spoken Response
  ```
- **Faster-Whisper STT Subsystem**: In-process singleton model caching (`tiny`, `base`, `small`, `turbo`), non-blocking threadpool execution (`asyncio.to_thread`), hardware auto-detection (CUDA / CPU + INT8).
- **VOICEVOX TTS Subsystem**: Japanese voice synthesis via HTTP engine (`/audio_query` + `/synthesis`), speaker voice catalog, and offline fallback resilience.
- **Conversation Engine & Prompts**: `ConversationPromptBuilder` with spoken Japanese constraints (1–3 sentences max), Persona JLPT levels (N5–N1), and dual modes: `Conversation` (pure immersion) and `Coaching` (gentle `💡 Better:` hints).
- **Context Window Manager**: `ConversationContextBuilder` retaining system prompt + recent $N$ dialogue turns.
- **Echo Prevention & Audio Suppression**: Microphones are muted during AI speech (`ai_speaking`) with anti-echo delay buffers.
- **Persistent Sessions & Turns**: Snapshot configurations, latency breakdown metrics (`stt_ms`, `ai_ms`, `tts_ms`, `total_ms`), and anti-duplicate `client_turn_id`.
- **Next.js Speaking Room UI**: Finite state machine (`listening`, `processing_stt`, `ai_thinking`, `ai_speaking`), animated Sakura waveform visualizer, live transcript stream with audio replay, session timer, and summary analytics.

### ✅ Phase 4 — Conversation Intelligence & Deep Correction
- **Asynchronous Deep Analysis Pipeline**:
  ```text
  User speaks ➔ Real-Time AI Response (Zero Blocking) ➔ Background Analysis Worker ➔ Multi-Stage Linguistic Pipeline ➔ Live Coaching & Review Dashboard
  ```
- **Pedagogical Prioritization Engine**:
  - `🔴 MUST_FIX`: Broken grammar, particle confusion, or ungrammatical conjugations (e.g. `見たです` ➔ `見ました / 見た`).
  - `🟠 SHOULD_FIX`: Situational politeness or formality mismatches against Persona role.
  - `⭐ NATIVE_ALTERNATIVE`: Grammatically valid phrases with natural native colloquialisms (e.g. `知っています` ➔ `知ってるよ`). Valid natural informal speech (e.g. `昨日はめっちゃ楽しかった`) is strictly protected and never marked wrong.
  - `⚪ IGNORE`: Minor stylistic preferences and conversational fillers.
- **Multi-Stage Analyzer Suite (`app/domains/conversation_intelligence`)**:
  - `CorrectionAnalyzer`: Correctness analysis with low-confidence STT guardrails.
  - `NaturalnessAnalyzer`: Native phrasing and colloquial spoken markers.
  - `ContextAnalyzer`: Keigo, persona hierarchy, and situational politeness.
  - `VocabularyAnalyzer` & `GrammarAnalyzer`: Pattern extraction and lexical alternatives.
  - `FeedbackPrioritizer`: Cognitive budgeting (max 3 prioritized issues per turn).
  - `SessionAnalyzer`: Holistic review, repeated pattern detection, and mandatory positive strengths.
  - `AnalysisOrchestrator`: Multi-stage coordinator with cost-aware bypass for short acknowledgments (`はい`, `なるほど`).
- **Resilient Background Worker & Hybrid Queue**: Asynchronous `AnalysisWorker` with Redis support and in-memory `asyncio.Queue` fallback.
- **Interactive UI & Review Dashboard**:
  - **Live Coaching Card**: Instant compact tip with before/after diff and audio playback.
  - **Conversation Intelligence Drawer**: Collapsible live stream of turn-by-turn analysis.
  - **Session Review Dashboard**: Post-session tabs for 🟢 Strengths, 🔴 Must Fix & 🟠 Should Fix, ⭐ Native Expressions, 🔁 Repeated Patterns, and 💡 Top 3 Actionable Recommendations.
  - **Learner Rating System**: 👍 Helpful / 👎 Not helpful / ⚠️ Wrong correction feedback.

### ✅ Phase 5 — Learner Memory & Error Intelligence
- **Long-Term Learner Profile & Error Memory Architecture**:
  ```text
  Every Conversation ➔ Turn & Session Analysis ➔ Extract Learning Signals ➔ Update Learner Memory ➔ Detect Recurring Weaknesses ➔ Update Learner Profile ➔ Personalized Recommendations
  ```
- **Domain Schema & Database Models (`app/domains/learner_memory`)**:
  - `LearnerMemory`: Persistent long-term memory records with `uq_learner_memory_user_key` uniqueness constraint, tracking `confidence` $[0.0, 1.0]$ vs `mastery` $[0.0, 1.0]$ separately.
  - `MemoryEvidence`: Cumulative, immutable evidence log with `uq_memory_evidence_source` deduplication guarantee.
  - `LearnerProfile`: Holistic learner speaking profile with JLPT anchor, 4 sub-skill levels (Grammar, Vocabulary, Fluency, Naturalness), response speed, and AI diagnostic synthesis.
  - `MemoryFeedback`: User audit feedback store (`dismiss`, `restore`, `mark_inaccurate`).
- **Deterministic Mathematical Intelligence (Code-Driven Precision)**:
  - `MemoryKeyResolver`: Canonical key normalization (`particle.ha_vs_ga`, `grammar.wake_de_wa_nai`, `filler.excessive_nanka`, `politeness.keigo_avoidance`).
  - `MemoryExtractor`: Centralized evidence weighting (`MUST_FIX` = 1.0, `SHOULD_FIX` = 0.6, `SESSION_PATTERN` = 1.2, `CORRECT_USAGE` = 0.7, `STRENGTH` = 0.8).
  - `MemoryMerger`: Idempotent deduplication across multiple sessions and regression detection.
  - `MemoryScorer`:
    $$\text{Confidence} = \min\left(1.0, 0.35 + 0.15 \cdot \log_2(1 + \text{evidence\_count}) + 0.20 \cdot \frac{\text{unique\_sessions}}{\text{target\_sessions}}\right)$$
    $$\text{Weakness Priority} = (\text{severity} \cdot 0.35 + \text{recurrence} \cdot 0.25 + \text{recency} \cdot 0.20 + (1 - \text{mastery}) \cdot 0.20 + \text{regression\_boost}) \cdot \text{confidence}$$
  - `TrendAnalyzer`: Window-based deterministic progression detection (`new`, `improving`, `stable`, `worsening`, `resolved`).
  - `MasteryEstimator`: Accuracy curve + multi-context variety bonus (casual, workplace, travel, interview).
  - `LevelAssessor`: Dynamic speaking level estimator with `insufficient_evidence` uncertainty indicator for $< 3$ sessions.
- **Context Retrieval & Prompt Safety Delimiters**:
  - `MemoryRetriever`: Dynamic Top-K high-priority memory retrieval with token budget enforcement.
  - **Prompt Injection Defense**: Memory data isolated inside `<learner_memory> ... </learner_memory>` data tags.
- **Asynchronous Background Processing**:
  - `LearnerMemoryWorker`: Background task updating long-term learner memory automatically upon session analysis completion without blocking real-time speech.
- **Frontend Dashboard (学習者カルテ)**:
  - **Estimated Speaking Level Card**: Level estimation, JLPT anchor, sub-skill levels, and reflex latency.
  - **AI Coach Diagnostic Summary**: Cached qualitative evaluation synthesized via `AIRouter`.
  - **Top Weaknesses & Verified Strengths Cards**: Filtered views with trend badges, mastery progress bars, evidence counts, and context tags.
  - **Adaptive Learning Priorities**: Phase 7 preview with priority ranks, rationale, and direct practice triggers.
  - **Evidence Explorer Modal**: Timestamped audit trail of exact user utterances vs corrected sentences, with user dismiss/restore/report controls.

### ✅ Phase 6 — Pronunciation Engine & Japanese Pronunciation Intelligence
- **Audio-Level Acoustic Intelligence Pipeline**:
  ```text
  User Audio (16kHz Mono) ➔ Audio Quality & VAD ➔ Reading & Mora Resolution ➔ Dynamic Alignment ➔ 5 Acoustic Analyzers ➔ Weighted Scorer ➔ Feedback Prioritizer ➔ Learner Memory Ingestion
  ```
- **Japanese Linguistic Layer (`app/domains/pronunciation/japanese`)**:
  - `JapaneseReadingResolver`: Kanji-to-Kana reading resolution via `pykakasi` with Katakana normalizer.
  - `JapaneseMoraAnalyzer`: Discrete mora segmentation, phonemic mapping, and special mora isolation (Sokuon `っ`, Chōonpu `ー`, Hatsuon `ん`, Yōon `ゃ・ゅ・ょ`).
  - `PitchAccentTargetResolver`: Tokyo Japanese Pitch Accent pattern classifier (`⓪ Heiban`, `① Atamadaka`, `②+ Nakadaka`, `Odaka`) and expected level sequence (`[L, H, H...]`, `[H, L, L...]`).
  - `JapanesePronunciationIssueTaxonomy`: Structured taxonomy with pedagogical Vietnamese advice and practice tips.
- **5 Acoustic Analyzers (`app/domains/pronunciation/analyzers`)**:
  - `PhonemeAnalyzer`: Sound substitution matrix (Japanese R vs English L/R, Fu, Tsu, Shi/Chi, Voicing/Devoicing pairs).
  - `MoraTimingAnalyzer`: Japanese mora isochrony, long vowel extension ratio ($>0.7\times$ vs single mora), and Sokuon pause timing.
  - `PitchAnalyzerComponent`: Normalized Cross-Correlation (NCCF) fundamental frequency ($F_0$) extraction with speaker-relative semitone normalization ($12 \cdot \log_2(F_0 / \text{median}(F_0))$) and Tokyo contour pattern matching.
  - `RhythmAnalyzer`: Speaking tempo (mora/second) against learner targets ($3.5 - 7.0$ mora/s) and hesitation pause distribution ($>450$ms).
  - `IntonationAnalyzer`: Phrase contour smoothness and sentence-final pattern detection (question rise $\uparrow$ vs statement fall $\downarrow$).
- **Multi-Pillar Weighted Scoring & Dynamic Availability**:
  - Dynamic weights: Phoneme ($25\%$), Mora Timing ($25\%$), Pitch Accent ($20\%$), Rhythm ($15\%$), Intonation ($15\%$).
  - Partial availability support: If high background noise obscures pitch extraction, weight redistributes proportionally among available analyzers without faking 0.
- **Pedagogical Prioritization & Phase 5 Learner Memory Ingestion**:
  - `PronunciationFeedbackPrioritizer`: Ranks issues by linguistic contrast severity, cognitive budgeting (Top 3 Focus), and positive strengths.
  - `PronunciationLearningSignalExtractor`: Converts pronunciation weaknesses and strengths into `MemoryCandidate` records (`pronunciation.long_vowel`, `pronunciation.small_tsu`, `pronunciation.n_sound`, `pronunciation.phoneme.r`, `pitch_accent.heiban`, etc.) to update `LearnerMemory` and `LearnerProfile` automatically.
- **Background Worker & Sampled Queue**:
  - `PronunciationJobQueue` (Redis with async queue fallback) & `PronunciationWorker` processing audio without blocking real-time conversations.
  - `PronunciationSamplingPolicy`: Dynamic sampling for conversation vs coaching vs dedicated practice modes.
- **Interactive Visual Feedback Dashboard**:
  - **`PronunciationDashboard`**: Overall score gauge, tier badge, 5 pillar cards, and collapsible acoustic metadata.
  - **`MoraTimeline`**: Horizontal interactive mora strip with ✓/⚠ markers and timing metrics.
  - **`PitchContourChart`**: SVG F₀ pitch curve visualization with Tokyo Accent target overlay and semitone axis.
  - **`PronunciationFeedbackPanel`**: Top 3 prioritized issues, practice tips, and positive strengths.
  - **`AttemptComparisonStrip`**: Immediate retry progression (Attempt 1 ➔ 2 ➔ 3) with delta progress highlights.
  - **`RecordingQualityBadge`**: Usability and SNR indicator.
  - **Dedicated Practice Coach (`/speaking/pronunciation`)**: Curated practice targets, voice recording, reference synthesis, and instant feedback loop.

### ✅ Phase 7 — Learning Engine & Adaptive Curriculum
- **Closed-Loop Adaptive Learning Architecture**:
  ```text
  Learner State (Memory + Pronunciation + Analysis + Goals)
         ↓
  Deterministic Priority Engine
         ↓
  Speaking-First Daily Plan Generator (10/20/30/45 min budgets)
         ↓
  Template-First + AI-Personalized Exercises
         ↓
  Interactive Practice (Speech / Text / Audio)
         ↓
  Hybrid Exercise Evaluator (Deterministic + Phase 4/6 Signals + AI)
         ↓
  Multi-Dimensional Mastery Engine & Spaced Review Scheduler
         ↓
  Updated Learner State & Next Adaptive Recommendations
  ```
- **Code vs. AI Separation of Responsibilities**:
  - **Code controls**: Priority ranking, mastery calculation, review scheduling, difficulty adjustment, time allocation, and deduplication.
  - **AI supports**: Exercise scenario wording, natural Japanese phrasing, recommendation explanation, and open-ended semantic assessment.
- **Core Domain Subsystems (`app/domains/learning`)**:
  - `LearnerStateService`: Snapshot read-model combining linguistic levels, top weaknesses/strengths, active goals, active items, and pronunciation priorities without raw DB dumps.
  - `LearningItemService`: Manages active training targets with stable identity keys (`grammar.わけではない`, `particle.ha_vs_ga`, `pronunciation.long_vowel`) separated from raw memory observations.
  - `MasteryEngine`: Multi-dimensional mastery model (Spontaneous Production: 45%, Production: 35%, Recognition: 10%, Context Variety: 10%) with saturation curves, independence multipliers (Independent $1.0\times$, Assisted $0.6\times$, Scaffolded $0.2\times$), forgetting decay, and lifecycle transitions (`discovered` ➔ `active` ➔ `practicing` ➔ `improving` ➔ `mastered` ➔ `maintenance` / `regressed`).
  - `PriorityEngine`: Deterministic priority formula factoring severity, recurrence, recency, mastery gap, goal relevance, communication impact, regression boosts, cooldown dampening, and diversity balancing.
  - `ReviewScheduler`: Spaced repetition scheduler customized for speaking production with streak tracking and due review queue filtering.
  - `DifficultyAdjuster`: Progressive scaffolding fading (`none` ➔ `keyword_hint` ➔ `sentence_starter` ➔ `structured_options`) and session fatigue safeguards.
  - `ExerciseVarietyPolicy`: Enforces speaking-first daily mix (40% conversation, 20% drills, 15% pronunciation, 10% review, 10% vocab, 5% exploration) and SHA-256 signature deduplication.
  - `ExerciseGenerator` & `ExerciseValidator`: Versioned template blueprints + AI personalization + safety validation + zero-crash template fallback guarantee.
  - `ExerciseEvaluator` & `ExerciseSessionService`: Hybrid evaluation of learner utterances, closed-loop mastery delta updates, and plan item completions.
  - `DailyPlanGenerator`: Persists and caches daily learning plans per date, ensuring stable refresh behavior across 10m, 20m, 30m, and 45m budgets.
  - `CurriculumEngine`: Dynamic milestone units and long-term goal pathways.
- **REST API Endpoints (`/api/v1/learning/*`)**:
  - `GET /api/v1/learning/today` — Cached daily plan
  - `POST /api/v1/learning/today/regenerate` — Force plan regeneration
  - `GET /api/v1/learning/priorities` — Ranked recommendations with Why/How
  - `GET /api/v1/learning/items` & `POST /api/v1/learning/items/{id}/practice` — Item management and quick drills
  - `GET /api/v1/learning/reviews` — Due spaced reviews
  - `POST /api/v1/learning/exercises/{id}/start` & `POST /api/v1/learning/exercises/{id}/submit` — Exercise lifecycle
  - `GET /api/v1/learning/curriculum` — Dynamic curriculum units
  - `POST /api/v1/learning/recalculate` — Background full recalculation
- **Interactive Web UI (`/learning`)**:
  - **`DailyPlanCard`**: Hero daily plan card with time budget buttons, focus banner, and ordered slots.
  - **`PriorityCard`**: Ranked weakness cards with mastery bar, why/how context, and practice triggers.
  - **`MasteryBar`**: Multi-dimensional mastery visual bar with evidence context.
  - **`ExerciseModal`**: Interactive speaking practice dialog with scaffolding hints, voice/text input, score gauge, and mastery delta ($+0.05$) feedback.
  - **`ReviewQueueCard`**: Due spaced repetition items with streak indicators.
  - **`CurriculumPathwayCard`**: Long-term milestone progress tracker.
  - **Sidebar Navigation Link**: Added `今日の学習` (Adaptive Learning) with `Sparkles` icon.

### ✅ Phase 8 — YouTube Shadowing Engine
- **End-to-End YouTube Ingestion & Linguistic Processing Pipeline**:
  ```text
  YouTube URL ➔ Metadata & Subtitle Ingestion ➔ Sentence Segmenter ➔ Linguistic Analysis & JLPT Scorer ➔ Personalized Candidate Selector ➔ Shadowing Studio UI
  ```
- **Domain Schema & Database Models (`app/domains/shadowing`)**:
  - `ShadowingVideo`: Video metadata, duration, difficulty, audio quality, channel info.
  - `ShadowingSegment`: Timestamped sentence segments with clean transcript, furigana, romaji, JLPT level, mora count, grammar/lexical tags, and target pronunciation flags.
  - `ShadowingExercise`: Practice sessions linked to segments with `shadow`, `echo`, `listen_and_repeat`, and `blind_shadow` modes.
  - `ShadowingAttempt`: User recordings, duration, score breakdowns, mora accuracy, and pitch stability.
  - `ShadowingBookmark`: User-saved segments with custom notes for quick review.
- **YouTube Ingestion & Whisper Subsystem (`app/domains/shadowing/youtube`)**:
  - `YouTubeUrlResolver`: Validates watch URLs, shorts, and embed links.
  - `YouTubeMetadataExtractor`: Extracts title, channel, duration, thumbnail, and tags.
  - `YouTubeTranscriptFetcher`: Multi-language track priority (`ja` manual ➔ auto-generated ➔ Whisper STT fallback).
  - `YouTubeWhisperAdapter`: Fast local fallback for videos lacking official Japanese subtitles.
- **Linguistic Intelligence & Candidate Selection**:
  - `TranscriptSegmenter`: Timestamp-aware sentence segmentation with Japanese punctuation boundary merging.
  - `LinguisticAnalyzer`: JLPT difficulty scoring (N5–N1), mora count, speech rate (mora/sec), grammar tags, and vocabulary definitions.
  - `TranscriptQualityEvaluator`: Rejects corrupted/non-Japanese transcripts.
  - `SpeakerSegmenter`: Distinguishes multiple speakers in dialogues.
  - `CandidateSelector`: Recommends optimal clips matching the learner's active weaknesses (e.g. long vowels, keigo, particles) and goals.
- **Shadowing Studio UI (`apps/web/features/shadowing`)**:
  - **`YoutubePlayer`**: IFrame API integration with millisecond seeking, speed adjustments (0.5x–2.0x), and automatic A-B looping.
  - **`TranscriptPanel`**: Interactive synchronized transcript with active segment highlight, furigana toggle, and instant translation.
  - **`SegmentDetailPanel`**: Vocabulary definitions, grammar notes, and target pronunciation focus badges.
  - **`ShadowingControls`**: Mode selector (`shadow`, `echo`, `repeat`, `blind`), recording trigger, and playback rate options.
  - **`ShadowingScoreDisplay`**: Radar breakdown of mora accuracy, rhythm/speed matching, and pitch stability.
  - **`RecommendedClipsPanel`**: Personalized candidate segments ranked by relevance to learner profile.

### ✅ Phase 9 — Advanced Audio & Voice Experience Platform
- **Centralized Audio Platform Architecture (`app/domains/audio`)**:
  ```text
  Audio Capture & VAD ➔ Audio Player & Queue ➔ Unified TTS Service (LRU Cache & Fallback) ➔ Audio Consumers
  ```
- **Unified Domain Contracts & Enums**:
  - `PlaybackState`, `RecordingState`, `TTSState`, `VoiceCapability`, `AudioQualityStatus`, `AudioErrorCode`.
  - `VoiceProfileDTO`, `TTSRequest`, `TTSResult`, `PlaybackPreset`, `AudioQualityReport`, `ProviderHealth`.
- **High-Performance Audio Infrastructure**:
  - `InMemoryTTSCache`: Thread-safe LRU in-memory cache with configurable TTL (30 mins) keyed by deterministic sha256 hashes of text, provider, voice ID, speed, and pitch.
  - `AudioQualityAnalyzer`: Real-time signal analysis calculating volume RMS/dB, background noise floor, SNR, and clipping detection ($>0.5\%$ threshold).
  - `VoiceService`: 4-tier deterministic voice resolution hierarchy:
    $$\text{Session Override} \rightarrow \text{Persona Setting} \rightarrow \text{User Default Profile} \rightarrow \text{System Default}$$
  - `TTSService`: Unified facade over speech engines with automatic fallback to standard voice upon connection dropouts.
  - `AudioService`: CRUD operations for user voice profiles, custom presets, audio preferences, and system diagnostics.
- **Frontend Audio Platform (`apps/web/features/audio`)**:
  - **8 Unified React Hooks**:
    - `useAudioPlayer`: Complete state machine playback manager with speed, looping, and blob cleanup.
    - `useAudioRecorder`: Microphone capture with device selection and error handling.
    - `useTTS`: Speech synthesis and preview hook.
    - `useAudioDevices`: Device enumeration and `sinkId` capability detection.
    - `useAudioSession`: Session coordinator preventing audio conflicts across features.
    - `useAudioQueue`: Sequential playlist queue manager with auto-advance.
    - `useVAD`: Voice activity detection with sensitivity calibration.
    - `useAudioLevelMeter`: Volume level meter and clipping alert hook.
  - **8 Reusable UI Components**:
    - `AudioPlayButton`: Compact play/pause/replay/spinner button.
    - `PlaybackControls`: Timeline seek bar, time display, speed selector, and repeat toggle.
    - `RecordingButton`: Recording trigger with animated pulse and states.
    - `RecordingWaveform`: Reactive multi-bar soundwave visualizer.
    - `AudioLevelMeter`: Color-coded level meter with clipping warnings.
    - `SpeedSelector`: Button group for playback rate ($0.75\text{x} - 1.25\text{x}$).
    - `VoiceSelector`: Searchable voice catalog with preview buttons and capability pills.
    - `VoicePreview`: Voice card with live sample audio trigger.
    - `MicrophoneCalibrationModal`: Step-by-step microphone test and quality analysis modal.
    - `AudioDiagnosticsCard`: Real-time health status card for VOICEVOX, Faster-Whisper, and cache stats.
### ✅ Phase 10 — RPG & Gamification Engine
- **Immutable XP Ledger (`XPTransaction`)**: Append-only transaction ledger with deduplication protection (`uq_user_event_dedup`).
- **Non-Linear Leveling Curve**: Scaled progression formula with 50 rank tiers from *見習い侍 (Apprentice Samurai)* to *伝説の達人 (Legendary Master)*.
- **Quest & Challenge Engine**: Daily rotating quests, weekly challenges, and 30+ achievement badges.
- **Skill Tree**: Japanese speaking skill nodes (Fluency, Naturalness, Grammar, Pronunciation) directly reflecting real `LearningItem` mastery.
- **Boss Battles**: High-stakes conversational challenges (*Job Interview Boss*, *Izakaya Boss*) with passing score thresholds and reward titles.

### ✅ Phase 11 — Analytics & Personal AI Coach
- **Progress Intelligence & Skill Radar**: 6-dimension evaluation matrix, velocity metrics, and dynamic JLPT estimation.
- **Weekly Review Engine**: Automated weekly reviews detailing strengths, persistent roadblocks, and study velocity.
- **Personal AI Coach**: Grounded interactive coach with live access to learner memory, error patterns, and *"Practice Now"* drill actions.

### ✅ Phase 12 — Performance, Reliability & AI Optimization
- **Faster-Whisper GPU Model Manager**: GPU CUDA auto-detection, thread-safe loading, and LRU eviction (max 2 models) with VRAM flush.
- **AI Task Tiers & Token Budgeting**: 3-tier task classification (`FAST`, `BALANCED`, `DEEP`) and `PromptBudgetGuard` token guardrails.
- **Worker Crash Recovery**: Automatic rescue of orphaned `processing` jobs on startup across all 7 background workers.
- **SQL Aggregation & Pool Tuning**: Single-query SQL aggregations replacing memory scans, PostgreSQL async pooling, and SQLite WAL pragmas.
- **Health & Diagnostics**: `/api/v1/health/workers`, `/api/v1/diagnostics/system`, `/models`, `/cache`.

### ✅ Phase 13 — Final Polish, Production Readiness & Audit
- **First-Time Learner Onboarding**: 4-step interactive onboarding with speaking goal, JLPT level, style preference, and microphone test.
- **Organized Navigation**: Structured sidebar sections (Core Training, AI Intelligence, RPG Dojo, Settings).
- **System Preflight Tool**: `python scripts/preflight.py` verifying DB, Redis fallback, STT, AI router, storage, and workers.
- **Data Integrity Auditor**: `python scripts/verify_data_integrity.py` cross-auditing XP ledger, memory, turns, and analyses.
- **100% Pass Rate**: 159 automated Pytest tests passing, 25 web routes cleanly compiled.

---

## Getting Started

### 1. Clone & Environment
```bash
# Copy sample environment configuration
cp .env.example .env
```

### 2. Backend Setup
```bash
cd apps/api

# Create & activate Python virtual environment (.venv)
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # On Windows PowerShell
# source .venv/bin/activate    # On macOS/Linux

# Install dependencies
pip install -e .
pip install faster-whisper pykakasi scipy aiosqlite redis python-multipart yt-dlp youtube-transcript-api

# Run system preflight check
python scripts/preflight.py

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
Swagger UI is accessible at `http://localhost:8000/docs`.

### 3. Frontend Setup
```bash
cd apps/web

# Install frontend dependencies
npm install

# Start Next.js dev server
npm run dev
```
Web UI is accessible at `http://localhost:3000`.
- **Dashboard**: `http://localhost:3000/dashboard`
- **Voice Speaking Room**: `http://localhost:3000/speaking`
- **YouTube Shadowing Studio**: `http://localhost:3000/shadowing`
- **Adaptive Daily Plan**: `http://localhost:3000/learning`
- **AI Coach**: `http://localhost:3000/coach`
- **Progress & Analytics**: `http://localhost:3000/progress`
- **RPG Dojo Hub**: `http://localhost:3000/game`
- **Quests**: `http://localhost:3000/quests`
- **Skill Tree**: `http://localhost:3000/skills`
- **Boss Battles**: `http://localhost:3000/bosses`
- **Achievements**: `http://localhost:3000/achievements`

### 4. Running Infrastructure & Speech Engines
```bash
# Start PostgreSQL & Redis (Optional - App includes SQLite & In-Memory fallback)
docker compose up -d

# Start VOICEVOX Engine (for local Japanese speech synthesis)
# Run locally on http://127.0.0.1:50021
```

### 5. Running Tests & Audits
```bash
# Backend pytest suite (159 automated unit & integration tests)
cd apps/api
pytest tests/ -v

# Run system preflight & data integrity check
python scripts/preflight.py
python scripts/verify_data_integrity.py

# Frontend production build & typecheck (25 routes)
cd apps/web
npm run build
```

---

## Directory Structure
```text
SpeakingTraining/
├── apps/
│   ├── api/                    # FastAPI Backend
│   │   ├── app/
│   │   │   ├── api/v1/         # REST Routers (audio, shadowing, learning, pronunciation, conversations, game, analytics, coach, ai, personas, settings)
│   │   │   ├── domains/        # Domain-driven modules (audio, shadowing, learning, pronunciation, learner_memory, conversation_intelligence, conversation, speech, ai, personas, settings, providers, users, gamification, analytics)
│   │   │   ├── core/           # Config & structured logging
│   │   │   └── infrastructure/ # DB session, Redis client, storage, schema sync
│   │   ├── scripts/            # Preflight, data integrity, and media cleanup tools
│   │   └── tests/              # Pytest test suite (159 tests)
│   └── web/                    # Next.js Frontend
│       ├── app/                # 25 Next.js App Router routes (/dashboard, /speaking, /shadowing, /learning, /coach, /progress, /game, /quests, /skills, /bosses, /achievements, /settings)
│       ├── features/           # Modular domain features (onboarding, gamification, speaking, shadowing, learning, audio)
│       ├── components/         # Shared UI components & Design System (Sidebar, AppShell, TopNav, UI primitives)
│       ├── hooks/              # Custom React hooks (useAudioPlayer, useAudioRecorder, useTTS, useShadowing, useLearningPlan, useGameProfile, useQuests, useStreak)
│       └── services/           # Typed API clients (audioApi, shadowingApi, learningApi, pronunciationApi, conversationApi, gameApi, analyticsApi, coachApi)
├── packages/
│   └── ai-contracts/           # Shared AI & Speech Contracts
├── infrastructure/
│   └── docker/                 # Docker Compose & service definitions
├── docs/                       # Architectural & operational docs
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

---

## License
MIT
