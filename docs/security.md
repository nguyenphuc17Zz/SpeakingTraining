# Security & Privacy Policy

## 1. Secret & Key Encryption
- All external AI provider credentials (Google Gemini, Groq, OpenRouter) are encrypted at rest using **AES-256 (Fernet)** with a 32-byte URL-safe base64 encryption key.
- Secrets are never logged to console, disk, or returned in plaintext to the web frontend (masked transmission format: `sk-••••••••1234`).

## 2. Input Validation & Resource Caps
- Audio upload endpoints enforce a strict **10 MB maximum payload cap** and validate audio MIME types.
- Text turn inputs enforce a strict **4,000 character maximum limit**.
- YouTube shadowing import restricts URLs to valid `youtube.com` / `youtu.be` regex patterns, preventing server-side arbitrary URL fetch abuse (SSRF).

## 3. Prompt Injection Guardrails
- All user-supplied transcripts, learner notes, and YouTube video captions are marked as untrusted learner content in system prompts.
- Instructions are strictly separated from conversational turns via structured XML and JSON schemas.

## 4. Privacy & Media Retention
- Temporary audio recordings generated during STT transcription are written to scoped system temp directories and cleared automatically via `python scripts/cleanup_media.py`.
- No raw audio or private conversations are transmitted to third parties other than the user's explicitly configured AI providers.
