# Mode 2 — 敬語・タメ口特訓 Keigo & Register Studio — Integration Plan

> **Sản phẩm:** Top-level `/keigo` (như `/reflex`), 5 sub-modes, deterministic-first, library-assisted, AI-fallback.
> **Nguyên tắc:** Không hard-code giant keigo dictionary; language facts → linguistic resources; learning policy → app; ambiguity → AI.

**Ngày:** 2026-08-27  
**Trạng thái:** Approved — Build  
**Quyết định lock:** facade `domains/japanese/`, route `top-level /keigo`, cho phép thêm `wordfreq/jamdict` nếu cần (hiện dùng `sudachipy+pykakasi` + AI fallback).

---

## 1. Kiến trúc

```
Linguistic Resources (Sudachi/pykakasi + pluggable corpus/jamdict)
         ↓
JapaneseLanguageResourceProvider {analyze, get_lemma/reading/pos, normalize, lookup}
         ↓
LexicalProvider + SocialContext → UchiSotoResolver → RegisterEngine → KeigoTransformationEngine → DoubleKeigoAnalyzer → PragmaticsEngine → Deterministic Evaluator → (high conf → result / low → AIRouter KEIGO_*)
```

Đặt facade mới `apps/api/app/domains/japanese/provider.py` (Protocol + SudachiAdapter), không coupled vendor. `pronunciation/japanese` giữ acoustics.

---

## 2. Tích hợp Learning Engine

```
Learning Engine
├── Conversation
├── Reflex Speaking (Mode 1)
├── Keigo Studio (Mode 2) ← NEW
│   ├── keigo_sonkeigo
│   ├── keigo_kenjougo
│   ├── keigo_teineigo
│   ├── keigo_transformation
│   └── keigo_context
├── Pronunciation/Shadowing/Review/Free
```

- Thêm `ExerciseType` 5 values `KEIGO_SONKEIGO/KENJOUGO/TEINEIGO/TRANSFORMATION/CONTEXT` (reuse `LearningItemType.POLITENESS` với `key=keigo.*`).
- Reuse `Exercise/ExerciseAttempt(metrics_json.keigo)/ExerciseTemplate/MasteryEngine/automaticity/ReviewScheduler/VarietyPolicy`, `GameEventPublisher`, `MetricEngine`, `CoachService`.
- Chỉ sửa prefix check `startswith(("reflex","keigo"))` ở `learning.py` và `learning_item_service.py`.

---

## 3. Phase A — Language Infrastructure

- **Provider:** `JapaneseLanguageResourceProvider` Protocol + `SudachiLanguageProvider` (wrap `reading_resolver`, sudachi dict, pykakasi, caches), `LexicalProvider` (lemma, reading, pos, verb_class, honorific_info), provenance `OFFICIAL_GUIDANCE/LEXICAL_RESOURCE/MORPHOLOGICAL_ANALYZER/CORPUS/PROJECT_RULE/AI_INFERENCE`.
- **Corpus:** `JapaneseCorpusProvider` Protocol `{frequency, collocation, register metadata}` với `WordfreqCorpusProvider` optional, fallback → templates+AI.
- **Social:** `SocialContext {speaker/listener/referent roles+groups, relationship, situation, register_target, business_context, familiarity/hierarchy}`, groups `UCHI/SOTO/UNKNOWN`, roles `SELF/CUSTOMER/MANAGER/...` (ontology app-level).
- **UchiSotoResolver:** `resolve_group, hierarchy, honorific_direction, subject_perspective, determine sonkeigo/kenjougo`.
- **RegisterEngine:** targets `TAMEGUCHI/POLITE/BUSINESS_POLITE/BUSINESS_KEIGO/VERY_FORMAL`, multidimensional (relationship, hierarchy, business context).

---

## 4. Phase B — Keigo Domain

- **TransformationEngine:** `analyze_source_register→resolve_context→identify_action→honorific_direction→candidate generation→validation→ranking` → `AnswerCandidate {text, grammatical_validity, register_fit, naturalness, confidence, source}`. Không hard-code hàng nghìn đáp án, sinh động từ resources + rules + AI.
- **DoubleKeigoAnalyzer:** phân loại `ACCEPTED_ESTABLISHED/GENERALLY_INAPPROPRIATE/CONTEXT_DEPENDENT` với severity/confidence, không `if multiple_honorifics: WRONG`.
- **PragmaticsEngine:** `GRAMMATICALLY_CORRECT + KEIGO_CORRECT + CONTEXTUALLY_AWKWARD` tách biệt.
- **ErrorMutationEngine:** valid → mutation operators (wrong direction, double keigo, missing humble, casual injection, UchiSoto inversion) → validate.
- **KeigoKnowledgeModel:** `KeigoLexicalAnalysis {lemma, category SONKEIGO/KENJOUGO_I/II/TEINEIGO/BIKAGO, register, provenance}` — small explicit overrides only.

---

## 5. Phase C — Learning Integration

- Templates `keigo.sonkeigo.v1` etc affinity `POLITENESS`, `ExerciseFactory` deterministic pools `KEIGO_POOL_*` + AI personalization `AITask.KEIGO_GENERATION` (`KEIGO_GEN_PROMPT_VERSION`).
- Evaluator: `ExerciseEvaluator` thêm nhánh `keigo` sau reflex (deterministic canonical check via `_norm_jp` + set `accepted` → sanitize AI confidence/score → completeness heuristic → `KeigoScoringPolicy` 7-10 dims, caps nếu incomplete/context wrong, fallback → `AIRouter` `KEIGO_EVALUATION` low temp JSON schema.
- Mastery reuse `dimension=automaticity`, adaptive difficulty deterministic (high acc+independence → increase social complexity, fast+wrong → reduce pressure).

---

## 6. Phase D — API/Audio/AI

- Prefer `POST /learning/exercises/generate {exercise_type: keigo_*}` + `POST /learning/exercises/{id}/submit {keigo_metrics}`, chỉ khi không đủ mới thêm `/keigo/*` orchestration (mirror `reflex.py`: `GET/POST /keigo/exercises/generate?sub_mode=keigo_*`, `POST /keigo/exercises/{id}/submit`, `GET /keigo/progress`, `GET /keigo/pressure-profiles`).
- Reuse `STTRouter/Faster-Whisper 16kHz`, `TTSRouter/VOICEVOX VoiceStyle.POLITE/PROFESSIONAL`, `useAudioRecorder 16kHz`, `useVAD high`, timer `useKeigoTimer` (re-export `useReflexTimer`).
- `AIRouter` thêm `KEIGO_GENERATION/KEIGO_EVALUATION` (2 tasks), `PromptBudgetGuard`, strict JSON, AI nhận deterministic evidence `{context, linguistic_analysis, candidates, known_rules, learner_answer}`.

---

## 7. Phase E — Frontend

- Route `apps/web/app/keigo/page.tsx` (top-level) như `app/reflex/page.tsx` 307 lines: `SUB_MODES [mixed, teineigo, sonkeigo, kenjougo, context]`, `PRESSURE same 5`, `DURATION 3/5/10/20`, `subtitleMode default japanese`.
- `features/keigo/hooks/useKeigoSession.ts` clone `useReflexSession` (phase idle→loading→prompt_playing→waiting→recording→evaluating→result, `resolveMixed` 30/30/20/20 adaptive placeholder, prefetch 2, `promptCompletedAt=performance.now()`), `useKeigoTimer` re-export.
- Components `KeigoPromptCard/RegisterBadge/UchiSotoIndicator`, `KeigoTimer`, `KeigoResultCard` (role/register/keigo/naturalness), `KeigoSessionSummary`, nav thêm `sidebar.tsx` `Kính ngữ 敬語 /keigo`, `bottom-nav.tsx` tab `Phản xạ→Kính ngữ`, `app-shell.tsx` mobile+command palette.

---

## 8. Phase F — Verification

- Unit: morphology, Uchi/Soto, register, double-keigo, scoring; Integration: AI disagreement, lexical failure, STT/TTS failure; E2E `/keigo` full flow; Architecture test: không có giant verb/keigo dict trong `domains/keigo/` (chỉ policy <300 lines), provider được query.
- Analytics 5 keys `keigo.role/register/keigo_accuracy/uchi_soto/naturalness`, Coach grounded, Gamification `keigo.*` events, failure fallback deterministic.

---

## 9. Files

- `apps/api/app/domains/japanese/provider.py`, `lexical_provider.py`, `corpus_provider.py`
- `apps/api/app/domains/keigo/{social_context,uchi_soto,register_engine,transformation_engine,double_keigo,pragmatics,contracts,scoring,exercise_factory,prompts}.py`
- `apps/api/app/domains/learning/{contracts,templates,prompts,exercise_evaluator,exercise_generator}.py` (extend)
- `apps/api/app/api/v1/keigo.py`, `app/api/router.py`
- `apps/web/app/keigo/page.tsx`, `apps/web/features/keigo/{hooks,components,services}/`

---

**Sign-off:** Approved 2026-08-27 — proceed Build A→F.
