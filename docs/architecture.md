# System Architecture

## 1. High-Level Vision
The **Japanese Speaking Training OS** is an AI-first, domain-driven learning platform designed for deep spoken Japanese immersion, real-time conversation, pronunciation analysis, and YouTube shadowing.

```
+-------------------------------------------------------------+
|               Next.js Web Frontend (apps/web)               |
|      Japanese / Anime Aesthetic UI, AppShell, Services      |
+-------------------------------------------------------------+
                              |
                     REST / WebSocket API
                              |
+-------------------------------------------------------------+
|                 FastAPI Backend (apps/api)                  |
|  +-------------------------------------------------------+  |
|  |                     API Layer (/api/v1)               |  |
|  +-------------------------------------------------------+  |
|  |                    Domain Layer                       |  |
|  |  [users]      [settings]      [providers]  [personas] |  |
|  |  [speech]     [conversation]  [learning]   [memory]   |  |
|  |  [shadowing]  [pronunciation] [gamify]     [analytics]|  |
|  +-------------------------------------------------------+  |
|  |                 Infrastructure Layer                  |  |
|  |  [SQLAlchemy 2.0]     [Redis Cache]   [Fernet Crypto] |  |
|  +-------------------------------------------------------+  |
+-------------------------------------------------------------+
          |                                  |
+-------------------+              +-------------------+
|  PostgreSQL 16    |              |      Redis 7      |
+-------------------+              +-------------------+
```

## 2. Backend Design Principles
- **Domain-Driven Modularity**: Every business concept resides in its own isolated domain under `app/domains/`. No bloated general `utils` or `services`.
- **Provider Decoupling**: Business logic never imports or binds to Gemini, Groq, or Whisper directly. Everything interacts via abstract `AIProvider`, `STTProvider`, and `TTSProvider` contracts.
- **Zero-Secret Leakage**: Secrets and API keys are AES/Fernet encrypted at rest, never logged, and masked (`sk-••••••••1234`) on client transfer.
- **Standardized Error Handling**: All HTTP exceptions and domain errors yield consistent `{ "error": { "code", "message", "details" } }` JSON responses.

## 3. Frontend Design Principles
- **Japanese / Anime Minimalist Aesthetic**: Deep ink dark mode, sakura accents, crisp kanji badges, glassmorphism cards, smooth Framer Motion transitions.
- **Service Layer Abstraction**: UI components never call `fetch()` directly. All communications go through `services/*` API clients.
- **Progressive Disclosure**: Phase 1 provides foundation shells and previews; upcoming phase features clearly indicate status.
