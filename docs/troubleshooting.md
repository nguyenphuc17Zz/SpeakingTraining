# Hanasu AI OS — Troubleshooting & Operations Guide

## Common Issues & Solutions

### 1. Microphone Not Working in Browser
- **Symptom**: Speaking Room displays *"Microphone permission denied"* or VU waveform is flat.
- **Cause**: Browser blocked microphone access or audio device is locked.
- **Check**: Look at the URL bar in Chrome/Firefox/Edge for the blocked mic icon.
- **Fix**: Click the padlock/mic icon in the browser address bar, select **Allow**, and reload the page or click *"Retry Permission"*.

---

### 2. Gemini API Key or Quota Errors
- **Symptom**: AI responses take too long or fail with `HTTP 429` / `QuotaExceeded`.
- **Cause**: Google Gemini API key reached its free tier rate limit.
- **Check**: Visit `Settings ➔ AI Configuration` or run `python scripts/preflight.py`.
- **Fix**: 
  1. Ensure a secondary Groq API key is configured in `Settings ➔ AI Configuration`.
  2. Set **Routing Mode** to `Auto` — the system will automatically fail over to Groq `Llama-3.3-70b-versatile` without interrupting your conversation.

---

### 3. VOICEVOX Engine Offline or Missing Audio
- **Symptom**: AI text responses stream in real-time, but audio playback does not play.
- **Cause**: VOICEVOX Engine software is not running locally on port `50021`.
- **Check**: Open `http://127.0.0.1:50021/version` in your browser.
- **Fix**:
  1. Download and start VOICEVOX Engine locally (or launch via Docker).
  2. The application will continue operating in text-first mode gracefully if VOICEVOX is offline.

---

### 4. Faster-Whisper GPU CUDA Acceleration
- **Symptom**: Transcription takes 1–2 seconds instead of <200ms.
- **Cause**: NVIDIA CUDA toolkit or cuDNN is not detected, falling back to CPU INT8.
- **Check**: Run `python scripts/preflight.py` to inspect hardware detection.
- **Fix**: Ensure NVIDIA drivers and CUDA 12.x / cuDNN are installed. Faster-Whisper will automatically switch from CPU to GPU mode on next restart.

---

### 5. Redis Offline
- **Symptom**: `preflight.py` logs `[WARN] Redis offline. In-memory graceful fallback mode ACTIVE`.
- **Cause**: Redis server is not running on `localhost:6379`.
- **Fix**: This is a harmless warning. The app includes full in-memory fallback queues and TTS caching. To enable persistent Redis, start Docker:
  ```bash
  docker-compose up -d redis
  ```

---

### 6. Database Migration / Column Errors on Startup
- **Symptom**: SQLite logs `no such column: ...`.
- **Fix**: Run `python scripts/preflight.py` or restart the backend. The built-in `sync_database_schema(engine)` utility will automatically inspect tables and append any missing columns via dynamic `ALTER TABLE`.
