# Phase 6 — Pronunciation Engine & Japanese Pronunciation Intelligence Plan & Documentation

## 1. Subsystem Architecture Overview

Pronunciation in the **Japanese Speaking Training OS** is an independent, multi-stage audio processing and phonetic intelligence subsystem:

```text
User Speech Audio (PCM/WAV)
        ↓
Audio Quality Validation & Preprocessing (16kHz mono normalization)
        ↓
Voice Activity Detection (VAD & pause/filler analysis)
        ↓
Japanese Reading Resolution (Kanji → Kana sequence via pykakasi)
        ↓
Mora Segmentation & Phoneme Breakdown
        ↓
Forced / Dynamic Alignment (WordTimestamp & Mora durations)
        ↓
┌────────────────────────────────────────────────────────┐
│  1. Phoneme Articulation Analyzer (Sound substitutions)│
│  2. Mora Timing Analyzer (Isochrony, Sokuon, Long Vowel)│
│  3. Pitch Extractor & Tokyo Accent Pattern Classifier  │
│  4. Rhythm & Speaking Rate Analyzer (Mora/sec)         │
│  5. Sentence-Final Intonation Analyzer (Rise vs Fall)  │
└────────────────────────────────────────────────────────┘
        ↓
Multi-Component Weighted Scorer & Tier Interpreter
        ↓
Prioritized Pedagogical Feedback Generator (Top 3 Focus)
        ↓
Learning Signal Extractor → Merged into LearnerMemory (Phase 5)
```

---

## 2. Distinction of Core Concepts

1. **Speech Recognition (STT / Faster-Whisper)**: Recognizes lexical words (`"what did you say"`).
2. **Pronunciation Engine**: Evaluates acoustic fidelity (`"how accurately did you produce the Japanese phonemes & moras"`).
3. **Natural Prosody & Pitch Accent**: Assesses Tokyo pitch height patterns, isochronous mora rhythm, and natural sentence intonation.

---

## 3. Core Algorithms & Linguistic Modeling

### 3.1 Mora Segmentation
- Single Kana (`か`, `き`, `く`, etc.) = 1 mora.
- Digraphs (Yōon / `きゃ`, `しゅ`, `ちょ`) = 1 mora.
- Sokuon (`っ`) = 1 mora.
- Hatsuon (`ん`) = 1 mora.
- Long Vowels (`ー`, `おばあさん` / `がっこう`) = 2 distinct moras with duration ratios tracked.

### 3.2 Speaker-Independent Pitch Extraction & Normalization
- $F_0$ extraction using Normalized Autocorrelation (NCCF) with parabolic interpolation across 20ms frames and 10ms hops.
- Semitone normalization relative to speaker's own median pitch:
  $$\text{Semitones} = 12 \cdot \log_2\left(\frac{F_0}{\text{Median}(F_0)}\right)$$
- Tokyo Dialect Rules:
  - Mora 1 and Mora 2 always have opposite pitch.
  - **Heiban (⓪)**: Low → High → High ...
  - **Atamadaka (①)**: High → Low → Low ...
  - **Nakadaka (②+)**: Low → High → Fall before word end.

### 3.3 Dynamic Scoring Weights & Partial Availability
$$\text{Overall Score} = \sum_{i \in \text{Available}} \text{Score}_i \times \frac{w_i}{\sum_{j \in \text{Available}} w_j}$$
- Default weights: Phoneme = 0.25, Mora Timing = 0.25, Pitch Accent = 0.20, Rhythm = 0.15, Intonation = 0.15.
- If pitch extraction is unavailable (due to high background noise or whispering), weight is redistributed dynamically without faking 0.

---

## 4. REST API & Background Queue

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/pronunciation/analyze` | Synchronous audio analysis & learner memory ingestion |
| `POST` | `/api/v1/pronunciation/enqueue` | Asynchronous enqueue to background worker |
| `GET` | `/api/v1/pronunciation/attempts/{id}` | Get attempt result, pitch curve, and feedback |
| `GET` | `/api/v1/pronunciation/history` | Get recent attempts history |
| `GET` | `/api/v1/pronunciation/stats` | Get aggregate 5-pillar pronunciation statistics |
| `GET` | `/api/v1/pronunciation/targets` | Get curated pronunciation practice targets |

---

## 5. Frontend Visual Components

1. **`PronunciationDashboard`**: Overall score gauge, 5 acoustic pillars, and tier badges.
2. **`MoraTimeline`**: Horizontal mora strip with ✓/⚠ markers and timing metrics.
3. **`PitchContourChart`**: SVG F₀ pitch curve visualization with Tokyo Accent overlays.
4. **`PronunciationFeedbackPanel`**: Top 3 prioritized issues, practice tips, and strengths.
5. **`AttemptComparisonStrip`**: Immediate progression across practice attempts.
6. **`/speaking/pronunciation`**: Dedicated Japanese Pronunciation Practice page.

---

## 6. Integration with Phase 5 Learner Memory

- `PronunciationLearningSignalExtractor` extracts typed `MemoryCandidate` items:
  - `pronunciation.long_vowel`
  - `pronunciation.small_tsu`
  - `pronunciation.n_sound`
  - `pronunciation.phoneme.r`
  - `pitch_accent.atamadaka`
  - `pitch_accent.heiban`
- Seamlessly ingested into `LearnerMemory` and long-term `LearnerProfile` without blocking realtime conversations.
