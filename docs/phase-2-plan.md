# Phase 2 — AI Provider & Model System Architecture

## 1. Overview & Goals
Phase 2 establishes the core **AI Provider & Model System** for the Japanese Speaking Training OS. It builds a decoupled, high-resilience layer that abstracts away LLM providers (Google Gemini, Groq, OpenRouter) and provides:
- Single normalized contract (`AIRequest` ➔ `AIResponse` / `AIStreamEvent`)
- Error taxonomy with intelligent retry and fallback policies
- Dynamic Provider and Model Registries with capability detection
- Health monitoring and circuit breaker foundation
- Secure encrypted credential handling at rest
- Detailed token and latency usage tracking
- Interactive AI Playground & Settings UI for testing and configuring AI routes

---

## 2. System Architecture

```text
Frontend (AI Playground & Settings)
   ↓ (REST / SSE)
FastAPI AI Layer (/api/v1/ai/*)
   ↓
AI Router
   ├── Routing Policy (Auto / Manual)
   ├── Health Check & Circuit Breaker
   ├── Capability Filter & Model Matcher
   └── Fallback & Retry Orchestrator
   ↓
Provider Adapters (Gemini / Groq / OpenRouter)
   ↓
Normalized Response / Streaming Events
   ↓
Usage Tracking & PostgreSQL Store (ai_usage_records)
```

---

## 3. Core Principles
1. **Zero Provider Leakage**: Domain logic (such as turn management, pronunciation, or grammar feedback) depends exclusively on `AIRouter` and normalized models (`AIRequest`, `AIResponse`), never on provider-specific SDK classes.
2. **Normalized Error Taxonomy**: Errors are mapped to standard classes (`ProviderAuthError`, `ProviderRateLimitError`, `ProviderQuotaError`, `ProviderTimeoutError`, `ProviderUnavailableError`, `ProviderInvalidRequestError`).
3. **Resilient Routing & Fallbacks**:
   - **Auto Mode**: Directs to healthy configured primary provider (Gemini); gracefully cascades to secondary (Groq) or tertiary (OpenRouter) on retryable errors.
   - **Manual Mode**: Enforces explicit user provider choices; only falls back if `allow_fallback` is explicitly enabled.
4. **Security by Default**: Credentials are encrypted with AES-256 (Fernet), masked in API responses, and never logged.

---

## 4. Provider Support
- **Google Gemini** (`v1beta` REST & SSE Streaming): Default high-fidelity Japanese provider. Models: `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.0-flash`.
- **Groq LPU** (OpenAI-compatible REST & SSE Streaming): Ultra-fast inference provider. Models: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768`.
- **OpenRouter** (Multi-model Gateway): Models: `anthropic/claude-3.5-sonnet`, `deepseek/deepseek-chat`.

---

## 5. Database Schema Additions
- **`ai_usage_records`**: Tracks user ID, request ID, provider, model, task, token metrics, latency, success status, and fallback path.
- **`user_settings`**: Extended with `routing_mode`, `fallback_enabled`, and `fallback_priority`.

---

## 6. Verification & Definition of Done
- Provider contract test suite passing.
- Gemini and Groq adapters tested with mocked and live HTTP interfaces.
- Router auto-fallback and retry test coverage.
- Usage tracking database persistence.
- Next.js AI Playground & Settings UI with live streaming and diagnostics.
