# Mode 1 — 瞬発力スピーキング Speed Reflex Speaking — Integration Plan

> **Think less. Speak faster.** — Luyện phản xạ nói
> Mode tích hợp trong Learning Engine, không phải hệ thống tách riêng.

**Ngày:** 2026-08-26  
**Trạng thái:** Approved — Build Mode  
**Decisions locked:** automaticity column, 4 ExerciseType mới, hybrid conjugation (deterministic + lib kana + AIRouter fallback), pressure/variety có setting.

---

## 1. Architecture Integration

### 1.1 Vị trí trong hệ thống
```
Learning Engine
├── Conversation (Phase 3/4)
├── Reflex Speaking ← Mode 1 (Phase 7 extended)
│   ├── Conjugation Blitz (A)
│   ├── Speed Q&A (B)
│   ├── Sentence Transformation Blitz (C)
│   └── Contextual Reaction (D)
│   └── (E/F/G reserved: Rapid Follow-up, Rapid Roleplay, Pressure Conversation)
├── Pronunciation (Phase 6)
├── Shadowing (Phase 8)
├── Review (SM-2)
└── Free Speaking
```

### 1.2 Dependency Map (reuse, zero duplication)
| Layer | Reuse | Không tạo mới |
|-------|-------|---------------|
| Exercise model | `Exercise`/`ExerciseAttempt` + `ExerciseType` enum | No `ReflexExercise` table |
| Mastery | `MasteryEngine` + `LearningItem` (thêm column) | No duplicate mastery engine |
| Generation | `ExerciseGenerator` + `ExerciseValidator` + `ExerciseVarietyPolicy` | No new generator |
| Evaluation | `ExerciseEvaluator` + `AIRouter` | No new LLM abstraction |
| Audio | `STTRouter`/`TTSRouter`/`WhisperModelManager`/`InMemoryTTSCache`/`AudioPlatform` | No new recorder/STT/TTS |
| VAD | `useAudioRecorder` + `useVAD` (web) + `VADAnalyzer` (backend) | No independent mic detector |
| Japanese utils | `JapaneseReadingResolver` + `JapaneseMoraAnalyzer` | No new kana engine |
| Gamification | `GameEventPublisher` → `XPTransaction` ledger | No direct XP |
| Analytics | `MetricEngine` + `CoachService` | No second analytics |
| AI routing | `AIRouter` + `PromptBudgetGuard` | No direct Gemini/Groq |

### 1.3 Execution Flow (critical path sync, rest async)
```
Prompt generate (ExerciseGenerator → AIRouter or template fallback)
↓
TTS synthesize (TTSRouter → AudioPlatform → InMemoryTTSCache)
↓
Playback → playback_completed event (AudioPlatform)
↓
Timer start (performance.now, presentation radial timer)
↓
VAD arm (useVAD high sensitivity) → detect speech_start
↓
Recording (useAudioRecorder 16kHz) → speech_end
↓
STT (STTRouter/Faster-Whisper) → raw_transcript + normalized_transcript
↓
Evaluator (deterministic conjugation first → AI semantic if needed)
↓
ReflexAssessment (7 dims) → ExerciseResult
↓
MasteryEngine (automaticity) + ReviewScheduler + LearningItemService
↓ (async background)
Analytics (MetricEngine) → Gamification (GameEventPublisher) → LearnerMemory (if meaningful) → Coach context
↓
ResultCard + Next question prefetch (1-2 ahead, TTS prefetch)
```
DB: `Exercise.extra_metadata.reflex_config = {sub_mode, timer_limit_ms, pressure_profile, prompt_audio_url, expected_forms, semantic_targets}`  
`ExerciseAttempt.metrics_json.reflex = {reaction_latency_ms, semantic_latency_ms, response_duration_ms, timer_limit_ms, timed_out, late_response, speech_confidence, pressure_level, independence}`

---

## 2. Exercise Types

### 2.1 Enum Extension (`app/domains/learning/contracts.py:73`)
```python
class ExerciseType(str, Enum):
    # existing 13 ...
    REFLEX_CONJUGATION = "reflex_conjugation"
    REFLEX_QNA = "reflex_qna"
    REFLEX_TRANSFORMATION = "reflex_transformation"
    REFLEX_CONTEXT = "reflex_context"
```

### 2.2 Templates (`templates/exercise_templates.py`)
- `reflex.conjugation.v1` affinity `CONJUGATION` — Conjugation Blitz
- `reflex.qna.v1` affinity `FLUENCY` — Speed Q&A
- `reflex.transformation.v1` affinity `GRAMMAR` — Transformation
- `reflex.context.v1` affinity `NATURALNESS` — Contextual Reaction
Fallback deterministic synthesis khi AI unavailable.

### 2.3 Generation Input
`learner_level, learned_grammar, mastery, recent_mistakes, target_conjugation, difficulty, frequency, verb_class, recent_signatures (SHA256 anti-repetition)`

---

## 3. Scoring — ReflexAssessment

### 3.1 Dimensions (mỗi dim: score 0-100 + confidence 0-1)
`reaction, accuracy, naturalness, fluency, context_fit, independence, completeness` → `overall` (weighted per sub-mode, server-owned policy).

**Weight policy:**
- Conjugation Blitz: accuracy 50 / reaction 30 / fluency 20
- Speed Q&A: context_fit 30 / grammar 25 / reaction 20 / naturalness 15 / fluency 10
- Contextual Reaction: context_fit 30 / naturalness 25 / grammar 20 / reaction 15 / fluency 10
- Transformation: transformation_correctness 40 / semantic_preservation 30 / reaction 15 / naturalness 15

### 3.2 No single universal score
Expose breakdown, không chỉ `82`. Frontend hiển thị `Reflex 82 + Reaction 91 + Grammar 88 + Naturalness 74 + Context 93 + Confidence Medium`.

### 3.3 Pressure Success States (không collapse)
`correct_and_fast / correct_but_slow / wrong_but_fast / wrong_and_slow / incomplete / timed_out / late_response / no_response`

---

## 4. Timer

### 4.1 Configurable Pressure Profiles
```
Relaxed: 6000ms
Normal: 4000ms (default)
Fast: 3000ms
Reflex: 2500ms
Extreme: 1500-2000ms
```
User chọn trong UI, Learning Engine recommend. Timer UI radial (normal/warning/critical), respect `prefers-reduced-motion`.

### 4.2 Timing Correctness
- `t0 = prompt playback_completed` (AudioPlatform event), không phải TTS request start.
- `t1 = first reliable voiced frame` (VAD confidence ≥ threshold).
- `reaction_latency = t1 - t0` (ms, `performance.now()` timestamps, không phải `setInterval` 1s).
- `semantic_response_latency = first meaningful lexical content - t0` (sau filler えーと/あの...).
- `response_duration_ms = speech_end - speech_start`.
- Lưu `null` nếu unavailable, không fake `0`.

---

## 5. Speech Detection (reuse AudioPlatform)

- Web: `useAudioRecorder` (MediaRecorder 16kHz, echoCancellation+noiseSuppression, volumeLevel via AnalyserNode) + `useVAD` thresholds `low 0.07/1400ms, medium 0.04/1000ms, high 0.025/700ms` → Reflex dùng `high` sensitivity.
- Backend: `VADAnalyzer` trong pronunciation pipeline.
- Robust handling: ambient noise, mouse clicks, background speech → confidence gating. Low confidence → latency unreliable → `null`.
- Overlap detection: nếu `speech_start` trước `prompt_completed` → `interrupted_prompt` → replay prompt (default).

---

## 6. Grammar Validation — JapaneseConjugationEngine

### 6.1 Service (`app/domains/reflex/conjugation_engine.py`)
Deterministic first, AI fallback only.

**Responsibilities:** `identify_verb_class → transform → generate_acceptable_variants → validate → explanation → canonical/alternatives`

**Supported targets (12):** 辞書形, ない形, た形, て形, 可能形, 受身形, 使役形, 使役受身形, 命令形, 意向形, ば形, たら形. Kiến trúc mở rộng.

**Verb classes:** ichidan (食べる), godan (書く/行く/話す...), irregular する/来る, 行く special handling (て→行って, 使役受身 variants).

**Acceptable variants:** `canonical_form`, `accepted_forms[]`, `alternative_forms[]`, `variant_notes[]`. Ví dụ:
```json
{"canonical": "行かせられる", "accepted": ["行かせられる", "行かされる"], "notes": "Both causative-passive variants accepted"}
```
Data model: `Exercise.acceptable_variants` + `extra_metadata.reflex_config.expected_forms`.

### 6.2 Hybrid libs
- Kana normalize: reuse `reading_resolver.py` (SudachiPy → pykakasi fallback) + `jaconv` nếu cần katakana/hiragana convert.
- Conjugation logic: pure Python rules (Godan stem tables, Ichidan -る→-られる, Irregular maps). Không hard-code logic trong frontend.
- LLM fallback: khi `confidence <0.7` hoặc verb hiếm → `AIRouter(task=REFLEX_EVALUATION, response_format=JSON_SCHEMA, temp 0.2)` để resolve ambiguity.

### 6.3 Question Generation
Deterministic template + AI personalization (`ExerciseGenerator`). Inputs: learner level, mastery, mistakes, verb class, frequency. Tránh obscure vocab trừ challenge mode.

### 6.4 Difficulty Dimensions
`verb_class, conjugation complexity, irregularity, target form, polarity/tense, context, speech pressure`. Progression: `食べる→ない (easy)` → `書く→て (normal)` → `行く→使役受身・過去 (hard)`.

---

## 7. Adaptive Difficulty & Mastery

### 7.1 Automaticity Dimension
Extend `LearningItem`:
```python
automaticity_mastery: float = 0.0  # [0.0,1.0]
```
Separate from `recognition/production/spontaneous/context_variety`. Stored as typed column (decision locked). Migration `010_reflex_automaticity.py`.

**Semantics:** `How quickly/independently can learner retrieve & produce pattern under pressure?` Example:
```
recognition 0.91
controlled 0.84
spontaneous 0.57
automaticity 0.41
```

**Update:** `MasteryEngine.calculate_mastery_delta(result, item, dimension="automaticity")` với `base_rate 0.08` (conservative), bounded `[-0.25,+0.20]`, saturation + independence multiplier. Reaction latency fast+correct+independent → modest increase (0.42→0.45), không jump 0.42→1.0. Decay tương tự `apply_decay` với `automaticity`.

**History:** per learning item `automaticity_history: [{latency_ms, timestamp}]` trong `extra_metadata` hoặc derived từ `ExerciseAttempt.metrics_json`.

### 7.2 Adaptive Pressure Rules (deterministic, min 5-10 comparable attempts)
- `accuracy high + reaction fast + confidence high` → pressure -500ms (slightly harder, max 1 tier per adjustment)
- `accuracy low OR context low` → decrease pressure hoặc simplify task
- `accuracy high BUT reaction slow` → keep difficulty, focus automaticity
- `reaction fast BUT accuracy low` → reduce pressure, reinforce correctness (không reward speed)

Implemented trong `DifficultyAdjuster.adjust_reflex_pressure()` + `adaptive_pressure` service.

### 7.3 Speed Profile (analytics read-model, không phải mastery engine riêng)
`SpeakingReflexProfile{reaction, semantic_response, grammar_automaticity, spontaneous_response, pressure_tolerance, threshold}`. Derived concept `pressure_tolerance`: accuracy vs timer curve (3s:92%, 2.5s:88%, 2s:83%, 1.5s:61% → threshold ~2.1s). Display as `"Current comfortable response window: 2.4–3.0s"`.

---

## 8. Analytics & AI Coach

### 8.1 Metrics (extend Phase 11 `MetricKey`)
```
reflex.reaction_latency (raw, p50, p90)
reflex.semantic_latency
reflex.accuracy
reflex.naturalness
reflex.automaticity
reflex.pressure_tolerance
reflex.timeout_rate
reflex.late_response_rate
reflex.independent_success_rate
reflex.accuracy_under_pressure
```
Store raw latency; normalize for comparison (timer limit, difficulty, prompt length). Only compare comparable attempts.

### 8.2 Coach Integration
Grounded insights:
- "Bạn làm đúng 91% Conjugation Blitz nhưng mất 2.7s → bottleneck là retrieval speed, không phải kiến thức chia thể."
- "Grammar 90% + Reaction 2.9s + Naturalness 81% → retrieval speed là vấn đề."
Evidence-based, wording `"Your data suggests..."` không `"This proves your brain..."`.

`Practice Now` → Learning Engine (đã có `RecommendationEngine`), không tạo exercise trực tiếp từ Coach.

---

## 9. Gamification Integration (reuse Phase 10)

Events qua `GameEventPublisher`:
```
reflex.exercise_started/completed/perfect/personal_best/streak/learning_item_improved/automaticity_improved
```
Gamification owns XP/combo/quest/achievement/boss. Policy:
- XP depends on difficulty+correctness+independence+improvement, không solely speed.
- Fast wrong = small reward; slower correct independent = normal/high.
- Anti-farming: diminishing returns cho identical `exercise_signature`, nhưng vẫn ghi learning evidence.
- Perfect = correct + context appropriate + independent + high confidence + reaction within target.
- Personal best chỉ compare comparable attempts (same exercise_type/difficulty/timer).
- Combo forgiving rules (trong `GameWorker`).

Achievements/quests examples (định nghĩa trong `GamificationSeeder`, không hard-code trong Reflex):
Boss/Quest: "Respond to 10 questions under 3s" → Learning objective belongs to Learning Engine, reward belongs to Gamification.

---

## 10. API

**Reuse existing `/api/v1/learning` endpoints (preferred):**
- `POST /learning/exercises/generate` với `exercise_type=reflex_*` + `difficulty` + hỗ trợ `reflex_config` trong `extra_metadata`.
- `POST /learning/exercises/{id}/start` → `ExerciseAttempt` (extend `ExerciseStartRequest` optional `reflex_metrics`).
- `POST /learning/exercises/{id}/submit` → extend `ExerciseSubmitRequest` với `reflex_metrics: {prompt_completed_at, speech_started_at, speech_ended_at, timer_limit_ms, timed_out, late_response, speech_confidence, independence}` (backward compat, optional).
- `GET /learning/items/{key}` trả `automaticity_mastery`.
- `GET /learning/priorities` có thể recommend `reflex_*` types.

**Optional new endpoints (chỉ nếu cần session orchestration):**
```
POST /api/v1/learning/reflex/session  (create session with sub_mode, pressure, duration 3/5/10/20min)
GET  /api/v1/learning/reflex/session/{id}
POST /api/v1/learning/reflex/exercises/generate (alias, thin wrapper)
GET  /api/v1/learning/reflex/progress?period=7d|30d
GET  /api/v1/learning/reflex/items/{learning_item_id}
```

---

## 11. Data Model

### 11.1 LearningItem Extension
```python
automaticity_mastery: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
# optional indexes
```
Migration `010_reflex_automaticity.py` (upgrade: add column + index; downgrade: drop).

### 11.2 Exercise / ExerciseAttempt
Reuse tables. Conventions:
- `Exercise.exercise_type in (reflex_conjugation, reflex_qna, reflex_transformation, reflex_context)`
- `Exercise.extra_metadata.reflex_config = {sub_mode, timer_limit_ms, pressure_profile, prompt_audio_key, expected_forms, semantic_targets, reading, acceptable_variants_override}`
- `ExerciseAttempt.metrics_json = {... existing + reflex: {reaction_latency_ms, semantic_latency_ms, response_duration_ms, timer_limit_ms, timed_out, late_response, interrupted_prompt, speech_confidence, thinking_stall_ms}}`
- `ExerciseAttempt.mastery_deltas_json` includes `automaticity` delta.

Indexes (only if query-driven):
```sql
CREATE INDEX ix_learning_items_automaticity ON learning_items(automaticity_mastery);
CREATE INDEX ix_exercises_type_user ON exercises(exercise_type, user_id);
CREATE INDEX ix_attempts_exercise_created ON exercise_attempts(exercise_id, created_at);
```

---

## 12. UI/UX

### 12.1 Routes
- `/speaking/reflex` — Mode selector (4 sub-modes), Pressure/Difficulty toggles, Subtitle mode (hidden/japanese/japanese+reading/vietnamese), Session duration (3/5/10/20).
- `/progress` — Add Reflex tab (latency trend, automaticity, pressure tolerance, accuracy under pressure, filters 7d/30d/All).
- Learning item detail — Show `automaticity` radar + `Recommended: Conjugation Blitz + Contextual Reaction [Practice]`.

### 12.2 Components
- `ReflexTimer` (radial, remaining ms, color transitions, reduced-motion).
- `ReflexPromptCard` (FuriganaRubyText, audio play, scenario context).
- `ReflexResultCard` (overall + dims breakdown, XP toast, latency badges).
- `ReflexSessionSummary` (24 questions, 83% acc, avg 1.82s, p50 1.54s, best 0.91s, pressure window, strong/needs work).
- `useReflexTimer` hook (countdown with `requestAnimationFrame`, onExpire, remainingMs).
- `useReflexSession` hook (state machine idle→playing_prompt→waiting→recording→evaluating→result→next, auto-next ON, prefetch 1-2, TTS prefetch via AudioPlatform cache).

### 12.3 UX Policies
- Timeout → `"Time's up"` (không `"FAIL"`), show expected answer, allow retry/slow mode/hint.
- Retry hints reduce independence (independent > hint > example > translation).
- No translation modes: A audio-only, B audio+text, C Vietnamese situation→Japanese, D image→Japanese, E Japanese→Japanese.
- Error handling: audio quality low → `"Audio quality too low, retry"`; STT low confidence → retry/fallback; TTS unavailable → show text if subtitles enabled.

---

## 13. Performance / Cost / Reliability

- Critical path sync: prompt→timer→record→STT→essential eval→result→next (không đợi analytics/gamification/memory).
- Conjugation fast path: deterministic conjugation check → immediate result, deep analysis background.
- Next question + TTS prefetch during result display (1-2 ahead, respects voice/speed/cache).
- Cost: LLM only cho creative prompts + semantic evaluation; code handles timer/latency/scoring/mastery/XP.
- Idempotency: `ExerciseAttempt` + `GameEventRecord.event_key` dedup (no duplicate XP).
- Provider fallback: conjugation still works if Gemini down (deterministic); Q&A fallback to template; TTS fallback to text.

---

## 14. Testing Strategy

### 14.1 Unit
- Conjugation: godan/ichidan/する/来る/行く specials, long forms (使役受身過去), accepted variants.
- Timer: reaction fixtures (prompt_end 10.000 / speech 11.250 =1.25s, exact deadline 2.99/3.0 valid, after deadline → late_response, no speech → no_response, noisy frame low confidence → null latency).
- Pressure adjustment: 5 attempts 95%/1.4s → harder; 55% → reduce; no huge jumps.
- Scoring: fast-wrong≠Perfect, slow-correct≠failure, hint reduces automaticity gain.

### 14.2 Integration
- Q&A multi-valid answers, semantic mismatch (週末何する? → 昨日映画を見た = context mismatch despite grammar correct).
- Provider failure, TTS/STT failure, idempotency, background processing.

### 14.3 E2E
User → `/speaking/reflex` → Mixed/Normal/5min → cycle Conjugation→Q&A→Transformation→Contextual → verify latency from audio timestamps, mastery/automaticity update, analytics metrics, XP, coach insight, daily plan recommendation.

### 14.4 Verification Scripts
- `tests/learning/test_reflex_conjugation_engine.py`
- `tests/learning/test_reflex_scoring.py`
- `tests/learning/test_reflex_adaptive_pressure.py`
- `tests/e2e/test_reflex_flow.py` (or manual API curl)

---

## 15. Implementation Phases (Build Order)

**Phase A — Foundation (DB + Contracts):**
1. Migration `010_reflex_automaticity.py`
2. `contracts.py`: ExerciseType 4 values + AITask.REFLEX_GENERATION/REFLEX_EVALUATION + ReflexAssessment schemas
3. `models.py`: LearningItem.automaticity_mastery + indexes
4. `schemas.py`: DTO extends (automaticity in LearningItemDTO, reflex_metrics in ExerciseSubmitRequest)

**Phase B — Domain Services:**
5. `app/domains/reflex/` (hoặc `app/domains/learning/reflex/`) — `conjugation_engine.py`, `pressure_profiles.py`, `scoring.py`
6. `templates/exercise_templates.py` 4 reflex templates
7. `mastery_engine.py` add automaticity support + `difficulty_adjuster.py` adaptive pressure
8. `exercise_evaluator.py` reflex branch + `prompts.py` reflex prompts
9. `learning_item_service.py` 3-dim → 4-dim mastery update

**Phase C — API:**
10. `api/v1/learning.py` extend generate/submit + optional `reflex.py` router
11. `analytics` metric definitions + `gamification` event seeds

**Phase D — Frontend:**
12. `features/reflex/hooks/useReflexTimer.ts`, `useReflexSession.ts`
13. `features/reflex/components/ReflexTimer.tsx`, `ReflexPromptCard.tsx`, `ReflexResultCard.tsx`, `ReflexSessionSummary.tsx`
14. `app/speaking/reflex/page.tsx` + `services/reflex-api.ts` + `types/reflex.ts`

**Phase E — Verification:**
15. Tests + manual E2E + final report.

---

## 16. Final Acceptance Criteria (theo spec #151)

Core: 4 sub-modes ✅  
Audio: TTS→playback_completed→VAD→record→STT + failure handling ✅  
Scoring: 7 dims + completeness + independence + confidence ✅  
Learning: automaticity + mastery update + adaptive pressure + priority integration ✅  
Analytics: 11 reflex metrics + comparable sessions ✅  
Gamification: events/combo/XP/personal best/quests ✅  
Coach: grounded diagnosis + Practice Now ✅  
UX: auto-next, timer, recording state, summary, progress ✅  
Reliability: idempotency, fallback, TTS/STT handling, background ✅  
Tests: conjugation/variants/reaction/Q&A/transform/context/pressure/provider/E2E ✅

---

## 17. Known Limitations & Follow-up

- STT normalization (kana/kanji) cần tuning sau với real Faster-Whisper data.
- Pressure threshold derivation cần ≥20 samples trước khi stable.
- Vocab frequency filter cần corpus integration (phase sau).
- E/F/G sub-modes (Rapid Follow-up/Roleplay/Pressure Conversation) reserved.

---

**Sign-off:** Approved by user 2026-08-26 — proceed to Build.
