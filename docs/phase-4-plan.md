# Phase 4 — Conversation Intelligence & Deep Correction Plan: Japanese Speaking Training OS

## 1. Overview & Vision
Phase 4 elevates the Japanese Speaking Training OS from an interactive voice chat into an **intelligent speaking coach**.

```text
User speaks Japanese
       ↓
Faster-Whisper STT
       ↓
AI Conversation Response & VOICEVOX TTS (Realtime Path — Zero Blocking)
       ↓
User continues conversation seamlessly
       ↓
[Background Async Analysis Job]
       ↓
Analysis Orchestrator & AI Router
   ├── Correctness Analyzer (Grammar, Particles, Conjugation)
   ├── Naturalness Analyzer (Colloquial vs Rigid, Native-like alternatives)
   ├── Context & Politeness Analyzer (Keigo, Persona role, Formality)
   ├── Vocabulary & Grammar Miner (Patterns & Word Choice)
   └── Feedback Prioritizer (Severity ranking: Must Fix, Should Fix, Native Alt, Ignore)
       ↓
Persistence (TurnAnalysis, Corrections, SessionAnalysis)
       ↓
Frontend Realtime Delivery:
   ├── Coaching Mode: Instant compact coaching tips
   ├── Conversation Mode: Non-intrusive "Feedback ready" drawer
   └── Session End: Comprehensive Review Dashboard (Strengths, Weaknesses, Top 3 Recommendations)
```

---

## 2. Core Architectural Principles

### 2.1 Complete Decoupling of Realtime Path vs Deep Analysis Path
- Realtime latency must remain sub-second without waiting for complex reasoning models.
- STT -> LLM response -> TTS plays immediately.
- Analysis tasks are dispatched asynchronously as background jobs.

### 2.2 Pedagogical Philosophy: Selective Correction over Over-Correction
- Differentiate **Must Fix** (broken grammar, meaning confusion) from **Native Alternative** (technically correct but native speakers say it differently) and **Ignore** (minor stylistic variance).
- A valid native phrase like `昨日はめっちゃ楽しかった` must **never** be labeled wrong!
- Explanations are delivered in friendly Vietnamese by default, maintaining an encouraging coach tone.

### 2.3 Whisper Uncertainty & Safety Guards
- Low-confidence or truncated transcripts are flagged to prevent blaming the user or issuing false `MUST_FIX` corrections.
- Strict prompt boundary isolation (`<learner_transcript>`) prevents prompt injection.

---

## 3. Domain Model & Database Schema

### 3.1 Domain Layout
`app/domains/conversation_intelligence/`
- `contracts.py`: Pydantic models, schemas, enums (`Severity`, `Category`, `Confidence`, `JobStatus`).
- `models.py`: SQLAlchemy models (`TurnAnalysis`, `AnalysisCorrection`, `GrammarNote`, `VocabularyNote`, `SessionAnalysis`, `AnalysisJob`, `AnalysisUserFeedback`).
- `prompts.py`: Versioned prompt templates (`conversation.analysis.v1`, `session.analysis.v1`).
- `analyzers/`: Modular analyzers (`CorrectionAnalyzer`, `NaturalnessAnalyzer`, `ContextAnalyzer`, `VocabularyAnalyzer`, `GrammarAnalyzer`, `FeedbackPrioritizer`, `SessionAnalyzer`).
- `orchestrator.py`: Multi-stage pipeline executor with caching and validation.
- `worker.py` & `queue.py`: Background job dispatcher.
- `service.py`: Domain service coordinator.
- `schemas.py`: API DTOs.

### 3.2 Tables
1. `turn_analyses`: Per-turn analysis records with quality score, metadata, prompt version, provider, model.
2. `analysis_corrections`: Individual correction items with original, corrected, explanation, native alternative, category, severity, confidence.
3. `grammar_notes`: Extracted grammar patterns and usage notes.
4. `vocabulary_notes`: Extracted vocabulary suggestions and alternatives.
5. `session_analyses`: Overall session review, mandatory strengths, weaknesses, repeated issue patterns, top 3 recommendations.
6. `analysis_jobs`: Async queue tracking (`queued`, `processing`, `completed`, `failed`).
7. `analysis_user_feedback`: User ratings (helpful, not helpful, wrong correction) and reasons.

---

## 4. API Endpoints (`/api/v1`)
- `GET /api/v1/conversations/{session_id}/analysis`: Get complete session analysis & turn analyses.
- `GET /api/v1/conversations/{session_id}/turns/{turn_id}/analysis`: Get analysis for a specific turn.
- `POST /api/v1/conversations/{session_id}/analysis`: Trigger or re-run session analysis.
- `POST /api/v1/conversations/{session_id}/turns/{turn_id}/analysis`: Trigger or re-run turn analysis.
- `POST /api/v1/analyses/{analysis_id}/feedback`: Submit user feedback on analysis/corrections.
- `GET /api/v1/analyses/jobs/{job_id}`: Check background analysis job status.

---

## 5. Frontend Features
- **Live Coaching Feedback Card**: Compact turn-by-turn guidance in Coaching Mode.
- **Interactive Diff & Word Highlighting**: Clickable error badges with before/after visual diffs and "▶ Listen to correction" TTS playback.
- **Review Drawer**: Clean, non-intrusive feedback inspector in Conversation Mode.
- **Comprehensive Session Review Dashboard**:
  - 🟢 Strengths (mandatory positive reinforcement)
  - 🔴 Must Fix & 🟠 Should Fix Breakdown
  - ⭐ Native Expressions & Colloquialisms
  - 📚 Grammar & 🧠 Vocabulary Insights
  - 💡 Top 3 Actionable Recommendations
- **User Feedback Actions**: Helpful 👍 / Not Helpful 👎 / Incorrect ⚠️.

---

## 6. Evaluation Dataset & Quality Testing
- 30 curated test cases (`tests/evaluations/fixtures/speaking_evaluation_cases.json`) spanning:
  - Correct sentences (verifying zero false positives)
  - Grammar & conjugation errors (`見たです` -> must detect)
  - Natural informal expressions (`めっちゃ楽しかった` -> must classify as valid native alt / correct)
  - Context & politeness mismatch (`どうも` to boss)
  - Whisper uncertainty handling
  - Prompt injection resilience
- Automated regression test suite.
