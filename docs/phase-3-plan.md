# Phase 3 — Voice Conversation MVP Plan: Japanese Speaking Training OS

## 1. Overview & Objectives
Phase 3 transforms the Japanese Speaking Training OS from a foundation shell into a **fully functioning, real-world Japanese voice conversation system**.

The end-to-end voice loop:
```text
User speaks Japanese into Browser Microphone
                    ↓
Web Audio API + VAD (Utterance Boundary Detection)
                    ↓
Audio Upload / Streaming
                    ↓
Faster-Whisper STT (Local / Accelerated)
                    ↓
Conversation Engine & Context Window Manager
                    ↓
AI Router (Gemini default / Groq fallback)
                    ↓
VOICEVOX TTS Engine (Japanese Speech Synthesis)
                    ↓
Browser Audio Playback & Microphone Suppression (Echo Prevention)
                    ↓
Continuous Multi-turn Conversation & Session Summary
```

---

## 2. Architectural Design & Separation of Concerns

### 2.1 Provider Independence
The `ConversationService` coordinates conversation state, turn progression, and context management **without knowing SDK details**. It interacts strictly via:
- `STTRouter` ➔ `STTProvider` (`FasterWhisperAdapter`)
- `AIRouter` ➔ `AIProvider` (`GeminiAdapter`, `GroqAdapter`, `OpenRouterAdapter`)
- `TTSRouter` ➔ `TTSProvider` (`VoicevoxAdapter`)

```text
                               ┌───────────────────────────┐
                               │     ConversationService   │
                               └─────────────┬─────────────┘
                  ┌──────────────────────────┼──────────────────────────┐
                  ▼                          ▼                          ▼
         ┌─────────────────┐       ┌───────────────────┐       ┌─────────────────┐
         │    STTRouter    │       │     AIRouter      │       │    TTSRouter    │
         └────────┬────────┘       └─────────┬─────────┘       └────────┬────────┘
                  ▼                          ▼                          ▼
       ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
       │FasterWhisperAdapter │    │Gemini/Groq Adapters │    │   VoicevoxAdapter   │
       └─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

---

## 3. Speech-to-Text (STT) Subsystem

### 3.1 Contract & Normalized Result
```python
class STTResult(BaseModel):
    text: str
    language: str = "ja"
    duration_ms: int | None = None
    confidence: float | None = None
    processing_time_ms: int | None = None
    model: str | None = None
    provider: str
    metadata: dict[str, Any] = {}
```

### 3.2 Faster-Whisper Implementation
- **Model Cache Lifecycle**: Models (`tiny`, `base`, `small`, `medium`, `large-v3`, `turbo`) are cached in-memory per `(model_name, device, compute_type)` — never reloaded on every turn.
- **Async Execution Safety**: Synchronous inference is executed via `asyncio.to_thread` or thread pools to **never block the FastAPI asyncio event loop**.
- **System Detection**: Automatic detection of CUDA / GPU availability with fallback to CPU + INT8/FP32.
- **Audio Preprocessing**: Temporary audio files are safely sanitized and guaranteed to be deleted after processing in a `finally` block.

---

## 4. Text-to-Speech (TTS) Subsystem

### 4.1 Contract & Normalized Output
```python
class TTSAudioOutput(BaseModel):
    audio_bytes: bytes
    format: str = "wav"
    duration_ms: int | None = None
    sample_rate: int = 24000
    voice: str
    provider: str
    model: str | None = None
    metadata: dict[str, Any] = {}
```

### 4.2 VOICEVOX Integration
- **Engine URL**: Configured via `VOICEVOX_ENGINE_URL` (default `http://127.0.0.1:50021`).
- **Two-Step Synthesis**: Calls `POST /audio_query` followed by `POST /synthesis`.
- **Speaker Discovery**: Calls `GET /speakers` to dynamically populate available character voices and styles.
- **Default Persona Mapping**:
  - *Friendly Senpai (Takeshi / Sakura)*: Natural conversational voice (e.g. Shikishima Ririko / Zundamon / WhiteCUL).
  - *Japanese Teacher (Sakura-sensei)*: Clear, articulate pacing (e.g. Tsugumi Hattori / Kasukabe Tsumugi).
  - *Interviewer (Tanaka-san)*: Formal, polite cadence (e.g. Namahage / Kurono Takehiro).
- **Resilience**: If the local VOICEVOX engine is offline or unreachable, returns a structured error with the AI text response intact, allowing the session to continue without crashing.

---

## 5. Conversation Engine & Prompt Philosophy

### 5.1 Persona Prompt Builder
Prompts are centrally constructed with strict constraints for **spoken natural Japanese**:
- **Conciseness**: Maximum 1 to 3 short sentences per turn to maintain conversational cadence (no long essays or bullet points).
- **Spoken Tone**: Casual *tameguchi* for peers, polite *desu/masu* or *keigo* for teachers/interviewers depending on persona.
- **Turn Continuation**: Naturally answers and asks one relevant follow-up question to keep the dialogue flowing.
- **Mode Adaptation**:
  - `conversation`: Pure natural immersion. No instant grammar correction.
  - `coaching`: Natural reply + gentle hint structured in response metadata.

### 5.2 Context Window Manager
- Injects System/Persona Prompt at index 0.
- Maintains the most recent $N$ dialogue turns (e.g., last 10 turns) to prevent context explosion while preserving short-term conversational memory.
- Prepares normalized `AIMessage` list for `AIRouter`.

---

## 6. Database Schema & Persistence

### 6.1 `conversation_sessions`
- `id`: UUID Primary Key
- `user_id`: Foreign Key to `users.id`
- `persona_id`: Foreign Key to `personas.id`
- `mode`: `"conversation"` | `"coaching"`
- `status`: `"active"` | `"completed"` | `"cancelled"` | `"error"`
- **Config Snapshots** (preserved across future setting changes):
  - `provider_preference`: e.g. `"gemini"`
  - `model_preference`: e.g. `"gemini-1.5-flash"`
  - `stt_provider_preference`: e.g. `"faster_whisper"`
  - `stt_model_preference`: e.g. `"base"`
  - `tts_provider_preference`: e.g. `"voicevox"`
  - `tts_voice_preference`: e.g. `"1"`
- `started_at`, `ended_at`, `duration_seconds`

### 6.2 `conversation_turns`
- `id`: UUID Primary Key
- `session_id`: Foreign Key to `conversation_sessions.id`
- `sequence`: Integer sequence (1, 2, 3...)
- `speaker`: `"user"` | `"assistant"`
- `transcript`: User speech or AI response text
- `client_turn_id`: Anti-duplicate idempotency key
- `stt_provider`, `stt_model`, `ai_provider`, `ai_model`, `tts_provider`, `tts_voice`
- `processing_time_ms`: Total execution time
- `metrics`: JSON dictionary with detailed latency breakdown (`vad_ms`, `stt_ms`, `ai_ms`, `tts_ms`, `total_ms`)
- `started_at`, `ended_at`, `created_at`

---

## 7. API Routes (`/api/v1`)

### 7.1 Conversation Endpoints (`/api/v1/conversations`)
- `POST /`: Initialize a new conversation session with selected persona, mode, and provider snapshot.
- `GET /{session_id}`: Retrieve session metadata and chronological turn history.
- `POST /{session_id}/audio-turn`: End-to-end multipart audio turn (Audio ➔ STT ➔ AI Context ➔ AI Router ➔ TTS ➔ Audio & Transcript response).
- `POST /{session_id}/turns`: Text-based turn (for manual input or testing).
- `POST /{session_id}/end`: Conclude session, compute durations, and persist final status.
- `GET /{session_id}/summary`: Generate session metrics (turn count, total speaking duration, avg latency, provider breakdown).

### 7.2 Speech Endpoints (`/api/v1/speech`)
- `POST /transcribe`: Standalone audio transcription using Faster-Whisper.
- `POST /synthesize`: Standalone text synthesis using VOICEVOX.
- `GET /voices`: List available TTS voices and speakers.
- `GET /stt-models`: List available STT models and hardware recommendations.

---

## 8. Frontend Speaking Feature (`apps/web/features/speaking`)

```text
apps/web/
├── features/speaking/
│   ├── components/
│   │   ├── ActiveSessionRoom.tsx       # Big mic button, status indicator, interactive room
│   │   ├── AudioVisualizer.tsx        # Pulsing anime / waveform visual feedback
│   │   ├── ConversationTranscript.tsx # Turn-by-turn chat with audio replay & hints
│   │   ├── MicrophonePermissionModal.tsx # Friendly troubleshooting & permission flow
│   │   ├── SessionLobby.tsx           # Setup (Persona, Mode, Simple/Advanced Providers)
│   │   └── SessionSummaryModal.tsx    # Completion summary with stats & Phase 4 placeholder
│   ├── hooks/
│   │   ├── useAudioPlayback.ts        # Audio player with cleanup and state
│   │   ├── useMicrophone.ts           # MediaStream, permission, stream teardown
│   │   ├── useSessionTimer.ts         # Active speaking & elapsed time tracker
│   │   ├── useVoiceActivityDetection.ts # Utterance detection with silence threshold
│   │   └── useVoiceSession.ts         # Master session orchestrator
│   ├── services/
│   │   ├── conversation-api.ts        # REST client for sessions and turns
│   │   └── speech-api.ts              # REST client for STT/TTS
│   ├── state/
│   │   └── session-state-machine.ts   # Explicit finite state machine
│   └── types/
│       └── index.ts                   # Strongly typed contracts
```

### 8.1 Finite State Machine
Explicit state transitions without conflicting boolean flags:
```text
[idle] ➔ [requesting_permission] ➔ [ready]
   │
   ├─► [listening] ──(speech detected + silence threshold)──► [processing_stt]
   │                                                                 │
   │                                                                 ▼
   │   [listening] ◄──(audio ended + delay)◄── [ai_speaking] ◄── [ai_thinking]
   │
   └─► [paused] / [ended] / [permission_denied] / [error]
```

### 8.2 Echo Prevention & Audio Cleanup
- When AI enters `ai_speaking`, microphone capture and VAD processing are strictly muted.
- After playback finishes, an intentional buffer delay (300ms) prevents room echo before re-enabling `listening`.
- On component unmount, all MediaStream audio tracks and AudioContext nodes are gracefully closed.

---

## 9. Verification & Testing Strategy

1. **Unit & Domain Tests**:
   - `test_conversation_context_builder.py`: Context window truncation, system prompt preservation.
   - `test_persona_prompts.py`: Persona prompt formatting, spoken Japanese guidelines, mode rules.
   - `test_stt_contracts.py` & `test_faster_whisper.py`: Faster-Whisper lifecycle, cache reuse, mocked inference.
   - `test_tts_contracts.py` & `test_voicevox.py`: VOICEVOX query generation, speaker listing, offline handling.
2. **API Integration Tests**:
   - `test_conversation_api.py`: Create session, audio turn processing, turn pagination, session conclusion, and summary.
   - `test_speech_api.py`: Direct STT and TTS endpoint validations.
3. **Frontend Diagnostics**:
   - State transition verification in `useVoiceSession`.
   - TypeScript compilation and Next.js lint validation.
4. **End-to-End Manual Verification**:
   - Verify microphone capture, Faster-Whisper transcription, Gemini/Groq LLM response generation, and VOICEVOX voice playback in the browser.
