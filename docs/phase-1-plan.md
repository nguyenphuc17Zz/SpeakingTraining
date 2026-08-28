# Phase 1 — Foundation Plan: Japanese Speaking AI Training OS

## 1. Overview & Goals
Phase 1 establishes a clean, modular, domain-driven foundation for the Japanese Speaking AI Training OS.
The architecture is designed to scale across future phases (realtime voice, YouTube shadowing, pronunciation scoring, learner memory, adaptive RPG engine) without requiring breaking rewrites.

## 2. Monorepo & System Architecture

```text
e:\SpeakingTraining/
├── apps/
│   ├── api/                    # FastAPI, SQLAlchemy, Alembic, Pydantic v2
│   └── web/                    # Next.js 14+ (App Router), TypeScript, Tailwind CSS, Lucide
├── packages/
│   └── ai-contracts/           # Shared types & schema contracts
├── infrastructure/
│   └── docker/
│       └── docker-compose.yml  # PostgreSQL 16 + Redis 7
├── docs/
│   ├── phase-1-plan.md
│   ├── architecture.md
│   ├── development.md
│   ├── environment.md
│   └── database.md
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

## 3. Backend Domains (Scaffolded & Extensible)
- **`users`**: Base user entity, profile, timezone, locale.
- **`settings`**: User preferences (theme, language, default AI provider/model, default TTS/STT).
- **`providers`**: Provider abstraction (`AIProvider`, `STTProvider`, `TTSProvider`), model capabilities registry, encrypted credentials store.
- **`personas`**: Persona management (name, speaking style, difficulty N5-N1, system seeds vs custom personas).
- **`conversation`**: Session state & session lifecycle models.
- **`speech`**, **`learning`**, **`memory`**, **`pronunciation`**, **`shadowing`**, **`gamification`**, **`analytics`**: Typed contracts & domain boundaries ready for implementation in subsequent phases.

## 4. Security & Cryptography
- Standard AES/Fernet encryption for all API keys stored in PostgreSQL.
- API keys masked (`sk-••••••••1234`) on GET responses; plaintext keys strictly in-memory during execution.
- Structured logger with secret-masking filters to prevent key leakage in logs.

## 5. Frontend & Japanese Aesthetic Shell
- Next.js 14 App Router with TypeScript.
- Centralized `api-client.ts` layer with typed service wrappers.
- Modern Japanese minimalist / anime aesthetic theme (Sakura accents, deep slate dark mode, clean typography, kanji chips, smooth transitions).
- Primary routes:
  - `/dashboard`: Daily mission, streak/XP stats, skill overview, recent activities.
  - `/speaking`: Persona selector & speaking lobby shell.
  - `/shadowing`: Shadowing study lobby shell.
  - `/progress`: Analytics & proficiency charts shell.
  - `/settings`: General, AI Providers (key management), Personas manager, Appearance.

## 6. Verification & Definition of Done
- Full test suite in `apps/api/tests/` (health, security encryption, settings, personas, provider credentials).
- Alembic database migration for foundation tables.
- Frontend build and lint checks pass.
- Complete documentation in `docs/` and root `README.md`.
