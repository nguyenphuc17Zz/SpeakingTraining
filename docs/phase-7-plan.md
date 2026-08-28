# Phase 7 — Learning Engine & Adaptive Curriculum Documentation

## 1. Executive Summary & Philosophy

Phase 7 establishes the **Adaptive Learning Engine** — the central intelligence brain of the **Japanese Speaking Training OS** that decides:
> *What the learner should practice next, why, using which exercise format, at what difficulty, when to review, and how to verify tangible speaking progress.*

### Product Philosophy
We reject static rigid curricula (`Lesson 1 → Lesson 2 → Lesson 3`). Instead, we implement a **closed-loop adaptive system**:

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

---

## 2. Core Architecture & Pure-Code Control

### Deterministic vs. AI Responsibilities

| Responsibility | Owner | Rationale |
|---|---|---|
| Priority Ranking | **Code** (`PriorityEngine`) | Objective, reproducible, auditable formula without LLM hallucinations |
| Mastery Score & Deltas | **Code** (`MasteryEngine`) | Bounded mathematical saturation, independence weighting, forgetting decay |
| Review Scheduling | **Code** (`ReviewScheduler`) | Spaced repetition intervals customized for speaking production |
| Difficulty & Scaffolding | **Code** (`DifficultyAdjuster`) | Session-level fatigue detection and progressive fading |
| Time Allocation | **Code** (`ExerciseVarietyPolicy`) | 40% conversation, 20% drills, 15% pronunciation, 10% review, 10% vocab, 5% exploration |
| Deduplication | **Code** (`ExerciseVarietyPolicy`) | SHA-256 exercise signature fingerprint matching |
| Exercise Wording & Scenarios | **AI** (`AIRouter` / `ExerciseGenerator`) | Natural, idiomatic Japanese phrasing and contextual variety |
| Open-Ended Evaluation | **AI** (`AIRouter` / `ExerciseEvaluator`) | Semantic flexibility without rigid exact string matching |
| Recommendation Explanation | **AI** (`AIRouter` / `LearningPrompts`) | Pedagogical wording grounded strictly on code-provided statistics |

---

## 3. Subsystem Breakdown

### 3.1 Learning State (`LearnerLearningState`)
Immutable snapshot read-model capturing:
- Current CEFR/JLPT linguistic level and level confidence
- Active user goals (Workplace, Interview, Speaking, Pronunciation, Travel, etc.)
- Top weaknesses and strengths from Phase 5 `LearnerMemory`
- Active `LearningItem` catalog with multi-dimensional mastery
- Overdue review queue from `ReviewScheduler`
- Pronunciation priorities from Phase 6 `PronunciationPracticeTarget`

### 3.2 Mastery Engine (`MasteryEngine`)
Multi-dimensional mastery model:
- **Recognition Mastery** ($w = 0.10$)
- **Production Mastery** ($w = 0.35$)
- **Spontaneous Production Mastery** ($w = 0.45$)
- **Context Variety Score** ($w = 0.10$)

Key dynamics:
- **Saturation curve**: Mastery delta shrinks smoothly as score approaches 1.0 (prevents skipping from 70% to 100% in a few attempts).
- **Independence weighting**: Completely independent production gives $1.0\times$ delta; assisted hint gives $0.6\times$; scaffolded example gives $0.2\times$.
- **Forgetting decay**: Exponential decay active only after 3 days of inactivity, decaying significantly slower for `mastered` / `maintenance` items.
- **Lifecycle state transitions**: `discovered` → `active` → `practicing` → `improving` → `mastered` → `maintenance` (or `regressed` upon relapse).

### 3.3 Priority Engine (`PriorityEngine`)
Deterministic priority score formula:
$$\text{Priority} = \text{Severity} \times \text{Recurrence} \times \text{Recency} \times \text{MasteryGap} \times \text{GoalRelevance} \times \text{CommImpact} \times (1 + \text{RegressionBoost} + \text{UncertaintyBoost})$$

- Includes **Cooldown Dampener** ($< 2$ hours since practice reduces priority to prevent rapid re-drill fatigue).
- Enforces **Diversity Balancing** (max 60% of top recommendations from any single skill type).

### 3.4 Spaced Review Scheduler (`ReviewScheduler`)
Customized for speaking production:
- Failed attempt ($\text{score} < 60$) → Reset streak, review in 1 day.
- Assisted success → Retain or increment streak slowly (interval: 2–4 days).
- Strong independent success ($\text{score} \ge 80$) → Advance streak, extend interval ($1 \to 2 \to 4 \to 7 \to 14 \to 28$ days).

### 3.5 Exercise Engine
- **Templates + AI Architecture**: Curated blueprint templates (`roleplay.grammar.v1`, `rapid_response.particle.v1`, `sentence_transformation.politeness.v1`, `pronunciation_repeat.pronunciation.v1`, `opinion.naturalness.v1`).
- **Validation Guard**: `ExerciseValidator` checks schema completeness, verifies reasonable durations ($1 \le \text{min} \le 45$), and guarantees no full answer sentence leaks in prompt instructions.
- **Zero-Crash Fallback**: If AI provider is unconfigured or unavailable, automatically falls back to deterministic template synthesis.

### 3.6 Daily Learning Plan (`DailyPlanGenerator`)
- **Plan Persistence**: Daily plan is persisted to database per `(user_id, plan_date)`. Refreshing the page returns the exact same plan with preserved progress.
- **Time Budget Fitting**: Adapts slot distribution dynamically for 10m, 20m, 30m, and 45m budgets.

---

## 4. REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/learning/today?time_budget=30` | Retrieves today's cached daily learning plan |
| `POST` | `/api/v1/learning/today/regenerate` | Forces regeneration of daily plan with new budget |
| `GET` | `/api/v1/learning/priorities?limit=5` | Returns top ranked, diversified recommendations with why/how |
| `GET` | `/api/v1/learning/items` | Lists all active linguistic learning items |
| `GET` | `/api/v1/learning/items/{id}` | Retrieves detailed learning item with mastery dimensions |
| `POST` | `/api/v1/learning/items/{id}/practice` | Creates an immediate targeted speaking drill for an item |
| `GET` | `/api/v1/learning/reviews` | Retrieves learning items due for spaced repetition |
| `GET` | `/api/v1/learning/goals` | Lists user learning goals |
| `POST` | `/api/v1/learning/goals` | Creates a new learning goal |
| `PATCH` | `/api/v1/learning/goals/{id}` | Updates a learning goal |
| `POST` | `/api/v1/learning/exercises/generate` | Generates a custom exercise targeting a specific key |
| `GET` | `/api/v1/learning/exercises/{id}` | Retrieves exercise metadata and instructions |
| `POST` | `/api/v1/learning/exercises/{id}/start` | Starts an exercise and creates an attempt record |
| `POST` | `/api/v1/learning/exercises/{id}/submit` | Evaluates response, updates mastery, and updates plan status |
| `GET` | `/api/v1/learning/curriculum` | Returns dynamic long-term curriculum units |
| `POST` | `/api/v1/learning/recalculate` | Enqueues background full recalculation (202 Accepted) |

---

## 5. Web Frontend

- **`/learning` (Dashboard)**:
  - **`DailyPlanCard`**: Hero plan card with time budget buttons, focus banner, and ordered slots.
  - **`PriorityCard`**: Ranked cards with mastery progress bars, why/how cards, and start buttons.
  - **`ReviewQueueCard`**: Due spaced reviews with streak indicators.
  - **`CurriculumPathwayCard`**: Long-term milestones with progress ratios.
  - **`ExerciseModal`**: Interactive practice dialog supporting scaffolding hints, speech/text submission, score gauge, and mastery delta ($+0.05$) visualization.
- Navigation link added to sidebar with `Sparkles` icon (`今日の学習`).

---

## 6. Verification & Test Suite

All 18 tests in `tests/learning/` pass with 100% success rate:
- `test_priority_engine.py`: Severity weighting, goal relevance boost, regression boost, diversity balancing.
- `test_mastery_engine.py`: Saturation curve, independence weighting, multidimensional combination, decay, lifecycle transitions.
- `test_review_scheduler.py`: Success interval extension, failure streak reset, due item filtering.
- `test_difficulty_and_validator.py`: Difficulty progression streaks, scaffolding triggers, fatigue detection, quality validation.
- `test_plan_and_variety.py`: Slot allocation by time budget, signature deduplication.
- `test_learning_e2e_flow.py`: Full closed-loop integration (Memory sync → State snapshot → Daily plan generation → Exercise start → Submission → Mastery delta update → Review scheduling).
