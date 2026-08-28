# Phase 5 — Learner Memory & Error Intelligence Plan: Japanese Speaking Training OS

## 1. Executive Summary & Vision
Phase 5 transforms the Japanese Speaking Training OS from isolated per-session coaching into an **intelligent, long-term learning partner**. 

```text
Every Conversation (Session)
         ↓
Deep Analysis (Phase 4)
         ↓
Extract Learning Signals (Grammar, Particles, Fillers, Keigo, Strengths, Goals)
         ↓
Deduplicate & Merge into Learner Memory (Layer 2)
         ↓
Update Evidence, Confidence, Recency, Trend & Mastery
         ↓
Recalculate Long-term Learner Profile (Layer 3)
         ↓
Context-Aware Memory Retrieval & Prompt Integration (Top K with strict budget)
         ↓
Next Conversation Persona Context (Subtle pedagogical awareness)
```

---

## 2. Three-Layer Memory Architecture

### Layer 1 — Session Memory (Ephemeral)
- Scope: Single conversation session.
- Components: Active turns, current topic/scenario, immediate mistakes, turn coaching tips.

### Layer 2 — Learner Memory (Cross-Session Persistent Knowledge)
- Scope: User-level persistent linguistic traits and patterns.
- Concept: Stable keys (`particle.ha_vs_ga`, `filler.nanka`, `politeness.keigo_avoidance`, `strength.response_speed`, etc.).
- Attributes: Evidence count, confidence ($0.0 \to 1.0$), severity, priority score, recency, trend, mastery ($0.0 \to 1.0$), lifecycle status.

### Layer 3 — Long-Term Learner Profile (Holistic Synthesis)
- Scope: Aggregate learning standing.
- Components: Estimated speaking level + confidence ("insufficient evidence" for new users), sub-skills (grammar, fluency, vocab, naturalness), top 5 weaknesses, top 5 strengths, active goals, AI-synthesized concise summary cache.

---

## 3. Core Principles & Deterministic Math

### 3.1 Evidence First
No memory exists without concrete evidence records (`MemoryEvidence`):
- Source session ID, turn ID, analysis ID, correction snippet.
- Weighting:
  - `MUST_FIX`: $1.0$
  - `SHOULD_FIX`: $0.6$
  - `NATIVE_ALTERNATIVE`: $0.3$
  - `IGNORE`: $0.0$ (rejected)
  - `STRENGTH`: $0.8$
  - `CORRECT_USAGE`: $0.7$

### 3.2 Deduplication & Stable Key Resolution
- `MemoryKeyResolver` resolves semantic variations (e.g. `particle は vs が`, `は/がの混同`, `ha/ga`) to canonical stable key `particle.ha_vs_ga`.
- Repeated occurrences increment evidence count, update attempt metrics, and refine trend instead of creating duplicate records.

### 3.3 Confidence Calculation
$$\text{confidence} = \min\left(1.0, 0.35 + 0.15 \cdot \log_2(1 + \text{evidence\_count}) + 0.20 \cdot \text{cross\_session\_ratio}\right)$$
Single observations with low analyzer confidence stay at low memory confidence.

### 3.4 Trend Detection (Deterministic)
- Compares error rate in recent sessions versus older session windows:
  - Error rate delta $\le -0.25 \implies \text{improving}$
  - Error rate delta $\ge +0.25 \implies \text{worsening}$
  - $\text{attempts} \ge 5$ and error rate $< 0.10$ and 0 recent errors $\implies \text{resolved}$
  - Previously $\text{resolved}$ but error returns $\implies \text{regression} \to \text{active}$
  - $\text{evidence\_count} \le 2 \implies \text{new}$
  - Otherwise $\implies \text{stable}$

### 3.5 Mastery & Context Variety
$$\text{mastery} = \min\left(1.0, \max\left(0.0, (\text{correct\_rate} \times 0.8 + \text{context\_bonus}) \times \text{recency\_weight}\right)\right)$$
Context bonus rewards correct usage across multiple scenarios (casual, workplace, travel, daily life).

### 3.6 Weakness & Strength Scoring
- **Weakness Priority**:
  $$\text{priority} = (\text{severity\_weight} \times 0.35 + \text{recurrence\_rate} \times 0.25 + \text{recency} \times 0.20 + (1.0 - \text{mastery}) \times 0.20) \times \text{confidence}$$
- **Strength Score**:
  $$\text{strength\_score} = (\text{consistency\_rate} \times 0.40 + \text{recency} \times 0.30 + \text{mastery} \times 0.30) \times \text{confidence}$$

---

## 4. Domain Structure (`app/domains/learner_memory/`)

```text
app/domains/learner_memory/
├── __init__.py
├── contracts.py              # Enums, Pydantic schemas, Priority DTOs, Context Budget DTOs
├── models.py                 # SQLAlchemy: LearnerMemory, MemoryEvidence, LearnerProfile, MemoryFeedback
├── key_resolver.py           # Canonical key resolution & taxonomy mapping
├── extractor.py              # Candidate extraction from TurnAnalysis & SessionAnalysis
├── merger.py                 # Memory deduplication, merging, and evidence attachment
├── scorer.py                 # Deterministic confidence, priority, and strength scoring
├── trend_analyzer.py         # Multi-session trend & regression detection
├── mastery.py                # Mastery estimation with context variety tracking
├── level_assessor.py         # Deterministic level estimation & uncertainty bounds
├── profile_service.py        # Profile aggregation & AI summary generation
├── retriever.py              # Context-aware top-K memory retriever with token budget
├── priority_service.py       # Adaptive learning priority API for Phase 7
├── queue.py                  # Redis & in-memory async job queue
├── worker.py                 # Background memory updater worker
└── service.py                # Main facade service for API & internal callers
```

---

## 5. Database Schema & Migration (`005_learner_memory_phase5.py`)

1. `learner_memories`:
   - `id` (UUID, PK), `user_id` (FK), `memory_type` (String), `key` (String, Index), `statement` (Text), `category` (String), `evidence_count` (Int), `confidence` (Float), `severity` (String), `severity_score` (Int), `priority_score` (Float), `mastery` (Float), `attempt_count` (Int), `correct_count` (Int), `error_count` (Int), `first_seen` (DateTime), `last_seen` (DateTime), `trend` (String), `status` (String), `is_regression` (Boolean), `contexts_used` (JSON), `extra_metadata` (JSON).
2. `memory_evidences`:
   - `id` (UUID, PK), `memory_id` (FK), `user_id` (FK), `session_id` (FK), `turn_id` (FK nullable), `turn_analysis_id` (FK nullable), `correction_id` (FK nullable), `evidence_type` (String), `weight` (Float), `original_snippet` (Text nullable), `corrected_snippet` (Text nullable), `context_tag` (String nullable), `created_at` (DateTime).
3. `learner_profiles`:
   - `id` (UUID, PK), `user_id` (FK unique), `overall_level` (String), `speaking_level` (String), `fluency_level` (String), `grammar_level` (String), `vocabulary_level` (String), `naturalness_level` (String), `confidence_score` (Float), `level_confidence` (String), `total_sessions_analyzed` (Int), `total_turns_analyzed` (Int), `avg_response_speed_ms` (Float nullable), `current_focus` (String nullable), `strengths` (JSON), `weaknesses` (JSON), `learning_goals` (JSON), `summary` (Text nullable), `summary_version` (Int), `summary_generated_at` (DateTime nullable), `last_recalculated_at` (DateTime).
4. `memory_feedback`:
   - `id` (UUID, PK), `memory_id` (FK), `user_id` (FK), `action` (String: dismiss, mark_inaccurate, restore), `feedback_text` (Text nullable), `created_at` (DateTime).

---

## 6. API Endpoints (`/api/v1/learner`)

- `GET /api/v1/learner/profile`: Holistic learner profile, levels, summary, top strengths/weaknesses.
- `GET /api/v1/learner/memories`: Filtered memory list (`type`, `status`, `trend`, `min_priority`).
- `GET /api/v1/learner/memories/{memory_id}`: Detailed memory record.
- `GET /api/v1/learner/memories/{memory_id}/evidence`: Evidence history linking to sessions/turns.
- `GET /api/v1/learner/weaknesses`: Ranked list of top learning weaknesses.
- `GET /api/v1/learner/strengths`: Ranked list of confirmed speaking strengths.
- `GET /api/v1/learner/goals`: Current user learning goals.
- `GET /api/v1/learner/priorities`: Top learning priorities contract for Phase 7.
- `POST /api/v1/learner/memories/{memory_id}/feedback`: Dismiss, mark inaccurate, or restore.
- `POST /api/v1/learner/profile/recalculate`: Explicit recalculation trigger.

---

## 7. AI Conversation Context Integration & Prompt Safety

In `ConversationContextBuilder`:
- `MemoryRetriever.get_compact_context(user_id, persona, topic)` selects top 3–8 items.
- Boundary protection:
```text
<learner_memory>
[Learner Profile Summary]
Level: Intermediate (Confidence: medium)
Top Weaknesses:
- Particle は vs が (Priority: High, Trend: Improving, Mastery: 45%)
- Formal/Keigo Avoidance (Priority: Medium, Trend: Stable)
Speaking Strengths:
- Rapid response speed & conversational continuity
Current Goal:
- Natural workplace communication
[Instruction to Persona]:
Adopt your persona naturally. Subtly present natural conversational opportunities around these topics without interrupting or lecturing robotically.
</learner_memory>
```

---

## 8. Frontend Learning Profile & Memory Dashboard

- Dedicated page at `/profile` (and updated navigation in `sidebar.tsx` + `/progress`).
- **Level & Mastery Overview**: Level badge, uncertainty/confidence, sub-skill metrics.
- **AI Learner Summary Card**: Human-readable synthesis with refresh indicator.
- **Top Weaknesses**: Interactive cards displaying trend badge, mastery progress bar, evidence count, success rate, and "View Evidence" trigger.
- **Top Strengths**: Positive reinforcement cards with evidence counts.
- **Evidence Explorer Drawer / Modal**: Detailed breakdown of observations across sessions/turns with before/after diffs.
- **User Correction Controls**: "Dismiss", "Mark as inaccurate", "Restore".

---

## 9. Testing & Quality Assurance Plan

1. **Unit & Domain Tests**:
   - `test_memory_key_resolver.py`: Canonical alias mappings and stability.
   - `test_memory_deduplication.py`: Multi-turn/multi-session deduplication into single memory.
   - `test_trend_and_mastery.py`: Deterministic trend transitions (improving, worsening, resolved, regression) and mastery progression.
   - `test_level_assessor.py`: Coarse level calculation and "insufficient evidence" handling.
   - `test_memory_retriever.py`: Context relevance filtering and budget enforcement.
2. **Evaluation Benchmarks**:
   - Multi-session progression scenario (`test_learner_memory_cross_session.py`):
     - Session 1: 3x は/が errors $\implies$ New active memory, low confidence.
     - Session 2: 2x は/が errors $\implies$ Merged memory, confidence $\uparrow$, priority $\uparrow$.
     - Session 3: 3x correct usages $\implies$ Trend $\to$ improving, mastery $\uparrow$.
     - Session 4: 2x correct in workplace context $\implies$ Context variety bonus, mastery $\uparrow$.
     - Session 5: 1x error $\implies$ Tracked attempt, regression/active status verified.
3. **API & End-to-End Integration Tests**:
   - API endpoints verification, background worker execution, idempotency on retry.
