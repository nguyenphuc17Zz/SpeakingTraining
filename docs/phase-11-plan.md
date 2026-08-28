# Phase 11 — Analytics & Personal AI Coach Architecture

## 1. Executive Summary

Phase 11 introduces the **Intelligence & Coaching Layer** for the Japanese Speaking Training OS.
Rather than acting as a static dashboard or generic LLM chatbot, Phase 11 synthesizes raw evidence from Phases 1–10 into **deterministic metrics, diagnostic bottleneck insights, and grounded coaching dialogues**.

### Core Architecture Philosophy
```
Evidence Layer (Existing Domain Tables)
      ↓
MetricEngine & TrendAnalyzer (Deterministic Math, Smoothing, Noise Guards)
      ↓
BottleneckAnalyzer & InsightEngine (Diagnostic Decision Trees, Cooldowns)
      ↓
GoalAnalyticsService & WeeklyReviewService (Facts Aggregation)
      ↓
CoachContextBuilder (Budget-capped, <learner_data> Prompt-safe Context)
      ↓
CoachService (Fast-path Deterministic Routing + Grounded AI Generation)
      ↓
Actionable Recommendations with [Practice now] CTAs
```

---

## 2. Metric Taxonomy & Registry

All derived metrics are strongly typed, versioned (`metric_version: "1.0.0"`), and registered in `METRIC_REGISTRY`:

| Metric Key | Name | Category | Unit | Min Sample Size |
|---|---|---|---|---|
| `fluency` | Speaking Fluency | speaking | pts | 3 |
| `naturalness` | Naturalness & Nuance | speaking | % | 3 |
| `grammar_accuracy` | Grammar Production | grammar | % | 3 |
| `vocabulary` | Vocabulary Variety | vocabulary | pts | 4 |
| `pronunciation_overall` | Pronunciation Overall | pronunciation | pts | 3 |
| `pitch_accuracy` | Pitch Accent Accuracy | pronunciation | % | 3 |
| `mora_timing` | Mora Timing & Rhythm | pronunciation | % | 3 |
| `intonation` | Sentence Intonation | pronunciation | % | 3 |
| `response_speed` | Response Latency | fluency | ms | 4 |
| `filler_rate` | Conversational Filler Rate | fluency | fillers/min | 3 |
| `self_correction` | Self-Correction Success | fluency | % | 3 |
| `conversation_depth` | Conversation Depth | speaking | turns/topic | 3 |
| `shadowing_score` | Shadowing Performance | shadowing | pts | 3 |
| `learning_consistency`| Practice Consistency | consistency | % | 7 |
| `goal_progress` | Goal Progress | goal | % | 3 |
| `exercise_success_rate`| Exercise Success Rate | learning | % | 4 |
| `mastery_delta` | Mastery Growth Delta | learning | Δ pts | 5 |
| `transfer_rate` | Spontaneous Transfer Rate | learning | % | 4 |

---

## 3. Key Components & Application Services

### 1. `MetricEngine` (`domains/analytics/application/metric_engine.py`)
- Reads without duplication from `pronunciation_attempts`, `conversation_sessions`, `turn_analyses`, `exercise_attempts`, `shadowing_segment_progress`, `daily_streak_activity`, `game_profiles`.
- Uses `TrendAnalyzer` to calculate EMA-smoothed deltas and confidence levels.

### 2. `TrendAnalyzer` (`domains/analytics/application/trend_analyzer.py`)
- Exponential moving average smoothing ($\alpha = 0.35$).
- Low-variance plateau detector ($\text{CV} \le 4\%$ over $\ge 5$ samples).
- Absolute noise margin guard (fluctuations within 3 pts remain `stable`).

### 3. `BottleneckAnalyzer` (`domains/analytics/application/bottleneck_analyzer.py`)
- Evaluates observable signals to identify primary limiting factor:
  - `Spontaneous Transfer Gap`: drill success $\ge 80\%$ but spontaneous transfer $< 55\%$.
  - `Grammar Production`: accuracy $< 65\%$.
  - `Response Latency`: grammar solid but latency $> 1800$ms.
  - `Naturalness & Nuance`: grammar $\ge 80\%$ but naturalness $< 70\%$.
  - `Mora Timing & Rhythm`: rhythm $< 65\%$.

### 4. `InsightEngine` (`domains/analytics/application/insight_engine.py`)
- Derives structured insights with 48h cooldown deduplication.
- Attaches direct action targets (`conversation`, `drill`, `shadowing`, `pronunciation`).

### 5. `GoalAnalyticsService` (`domains/analytics/application/goal_analytics_service.py`)
- Calculates milestone progress by mapping `LearningGoal` to active `LearningItem` masteries.

### 6. `WeeklyReviewService` (`domains/analytics/application/weekly_review_service.py`)
- Aggregates deterministic weekly facts (speaking minutes, session count, top wins, top weaknesses).
- Generates optional AI personalized narrative without altering the underlying numbers.

### 7. `CoachService` & `CoachContextBuilder`
- Deterministic routing for simple data questions (streak, minutes, weakness, recommendation).
- Deep coaching path via `AIRouter` with strict `<learner_data>` prompt isolation and zero-hallucination validation.
- Every coach recommendation includes a direct `[Practice now]` route.

---

## 4. Frontend Experience & Pages

- **`/progress`**: Interactive diagnostic dashboard with metric cards, trend badges, confidence indicators, bottleneck spotlight, insight feed, goal progress, and practice balance chart.
- **`/progress/weekly`**: Structured weekly report featuring key statistics, wins, focus areas, and AI coach commentary.
- **`/coach`**: Personal AI Coach chat interface with Daily Briefing banner, Quick Cards, suggested question chips, grounded answer bubbles with evidence transparency, and helpful/incorrect feedback toggles.

---

## 5. Verification & Quality Assurance

- **Backend Test Suite**: 147 tests passing (100% pass rate).
- **Web Production Build**: Next.js 14.2.3 compiled all 25 static & dynamic routes with zero TypeScript or JSX errors.
