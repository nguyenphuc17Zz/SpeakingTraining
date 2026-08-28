# AI Provider & Routing System

## Architecture Overview
The **AI Subsystem** provides unified multi-provider orchestration across Google Gemini, Groq LPU, and OpenRouter with automatic failover, task tier classification, token budgeting, and deduplication.

---

## 1. Unified Contracts
- `AIRequest`: Normalized prompt messages, parameters (temperature, max_tokens), response schema, and task tier.
- `AIResponse`: Normalized text content, token usage (`prompt_tokens`, `completion_tokens`), and latency breakdown.
- `AIStreamEvent`: Normalized Server-Sent Events stream chunks for real-time frontend token rendering.

---

## 2. Task Tier Mapping
Each AI task is categorized into one of three production tiers:
- **`FAST`**: Low latency, lightweight tasks (Fast grammar correction, inline vocabulary suggestions). Defaults to Groq `llama-3.3-70b-versatile` or `llama-3.1-8b-instant`.
- **`BALANCED`**: Real-time voice conversation, AI Coach interactions, and interactive drill grading. Defaults to Gemini `gemini-1.5-flash`.
- **`DEEP`**: In-depth multi-turn session linguistic analysis, weekly progress generation, and comprehensive speaking diagnostics. Defaults to Gemini `gemini-1.5-pro`.

---

## 3. Resilience & Optimization Guardrails
- **`AIRouter`**: Dynamically cascades from primary provider (e.g. Gemini) to secondary provider (e.g. Groq) upon network timeouts, rate limits, or HTTP 5xx errors.
- **`PromptBudgetGuard`**: Estimates token length (~2.5 chars/token) and dynamically compresses non-essential middle turns in long conversation histories.
- **`AIRequestDeduplicator`**: 60-second in-memory idempotency cache preventing double-click token waste on deterministic analysis and translation tasks.
- **Jittered Exponential Backoff**: Randomized retry intervals eliminate thundering-herd collisions during transient upstream outages.
