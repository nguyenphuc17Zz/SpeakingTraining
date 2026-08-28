# YouTube Shadowing Engine

## 1. Import Pipeline
```text
YouTube URL ➔ yt-dlp Audio Extraction ➔ Faster-Whisper Alignment ➔ Sentence Segmenter ➔ Shadowing Lesson
```
- Restricts URLs strictly to valid YouTube domains.
- Automatically extracts Japanese captions (or falls back to Faster-Whisper transcription).
- Groups raw word timestamps into natural spoken Japanese phrases (2–8 seconds per segment).

---

## 2. Shadowing Player & Assessment
- **Dual Subtitles**: Japanese kanji + Furigana reading alongside natural translations.
- **Listen & Shadow Mode**: Learner listens to native audio clip, records their voice utterance, and receives instant pronunciation & pitch fidelity feedback.
- **Looping & Speed Control**: Supports 0.75x, 0.9x, and 1.0x playback for fine-grained acoustic shadowing.
