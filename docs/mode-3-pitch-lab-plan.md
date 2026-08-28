# Mode 3 — 音調・モーラ特訓 Pitch Accent & Minimal Pairs Lab — Integration Plan

> **Top-level `/pitch` (Cao độ 高低), deterministic acoustic first, AI only khi ambiguity.**
> **Không hard-code giant pitch DB; facts qua provider; policy trong app.**

**Ngày:** 2026-08-27  
**Trạng thái:** Approved — Build  
**Lock:** Full stack pyopenjtalk + librosa pyin + parselmouth + WhisperX forced-align (guarded fallback → Sudachi autocorr proportional, label `estimated`).

---

## 1. Kiến trúc

```
Mode3
 ↓ JapaneseLanguageLayer (Sudachi morphology, ReadingResolver)
 ↓ JapanesePitchResourceProvider {lookup, get_reading/mora/accent_pattern, get_source_metadata} → Composite (OJAD/OpenJTalk → pyopenjtalk → librosa/parselmouth cross-check → AI unknown)
 ↓ ExerciseGenerator → User Audio / Reference
 ↓ Acoustic Layer: F0 (pyin/parselmouth, voiced masking, outlier, speaker semitone norm) → MoraAlignmentEngine (WhisperX DTW, fallback proportional) → AccentPatternExtractor (rise/fall/downstep) → DevoicingAnalyzer
 ↓ Scorer (pattern 40/mora 25/downstep 15/contour 10/stability 10, raw Hz không primary) → Feedback
 ↓ (high conf → result / low → AIRouter PITCH_*)
```

`apps/api/app/domains/pitch/` + `apps/api/app/domains/japanese/provider.py` facade.

---

## 2. Tích hợp Learning Engine

```
Learning Engine
├── Reflex, Keigo, Pitch Lab (Mode3)
│   ├── pitch_minimal_pair, mora_length, vowel_devoicing, pitch_contour, pitch_recognition
```

- Thêm `ExerciseType` 5 `PITCH_MINIMAL_PAIR/MORA_LENGTH/VOWEL_DEVOICING/PITCH_CONTOUR/PITCH_RECOGNITION`, reuse `LearningItemType pitch_accent`, `Exercise.extra_metadata.pitch_config {word_id, reading, mora_count, accent_type, pattern, resource_source, difficulty}`, `ExerciseAttempt.metrics_json.pitch`.
- Mở `is_timed` cho `pitch` trong `learning_item_service.py`.

---

## 3. Resource Layer

- **SudachiPy** reuse segmentation/lemma/POS.
- **pyopenjtalk** qua provider `lookup(text)->PitchLexicalEntry{reading,mora_count,accent_pos,pattern[H/L],drop,source,provenance}`, ẩn sau interface, provenance `OFFICIAL_GUIDANCE/LEXICAL_RESOURCE/CORPUS/ACOUSTIC_ESTIMATE/PROJECT_POLICY/AI_INFERENCE`.
- **librosa pyin** `fmin60 fmax500` primary, **parselmouth** Praat verify khi confidence thấp, output `PitchCurve {f0_hz, voiced_prob, time_ms, confidence}`, speaker normalize `12*log2(F0/median)` semitone.
- **CompositePitchResourceProvider** resolution `primary → secondary → estimator → AI → unknown`, không silent invent.

---

## 4. Acoustic

- **Mora:** reuse `JapaneseMoraAnalyzer` cho L/H pattern, `MoraAlignmentEngine` DTW WhisperX word timestamps → mora boundaries, fallback proportional với `_get_mora_weight`.
- **Downstep:** `expected_drop_mora` vs `observed_drop_mora` error major dù RMSE thấp.
- **Devoicing:** `です/ました/すき` probabilistic `devoicing_probability` dựa duration/energy/voicing/F0/spectral, không `u always disappears`.
- **Reference:** `VOICEVOX TTS` + `InMemoryTTSCache`, không coi 1 waveform là ground truth, multi-reference envelope khi có thể. Cache `resource_version + lexeme`.

---

## 5. Sinh động

- **MinimalPairGenerator:** query resource group by `normalized reading` → compare accent pattern → filter frequency/level → score difficulty.
- **MoraLength, Devoicing, Contour, Recognition** đều dynamic, không static list.

---

## 6. API/Frontend

- `POST /learning/exercises/generate {pitch_*}`, `POST /learning/exercises/{id}/submit {pitch_metrics}`, `GET /pitch/progress` (tương tự reflex), `GET /pitch/pressure-profiles` (Minimal Pair 4s, Mora 5s, Pitch Production 6s).
- Frontend `apps/web/app/pitch/page.tsx` top-level `Music2 高低`, `features/pitch/hooks/usePitchSession` clone `useReflexSession` + `usePitchTimer` + `useAudioRecorder/VAD high`, components `PitchModeSelector, MinimalPairCard, MoraLengthCard, DevoicingCard, PitchContourChart (reference/learner/mora/drop, reduced-motion), MoraTimeline, PitchResultCard`.

---

## 7. Verification

- Không giant accent dict / huge mora table, provider được query, DTW/acoustic deterministic, AI optional, audio-quality gate `RETRY_AUDIO` khi noisy/short/unstable, tests heiban/atamadaka/nakadaka/odaka + mora long/ん/っ + acoustic fixtures high/low pitch octave error.

**Sign-off:** Approved 2026-08-27 — Build A→F.
