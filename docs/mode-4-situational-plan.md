# Mode 4 — 実戦シミュレーション Situational Roleplay — Integration Plan

> **Top-level `/situations`, opt-in hands-free, 4 levels Guided/Standard/Challenge/Blind, deterministic state + AI dialogue.**
> **Không hard-code giant character/scenario DB; composable dimensions + provider + AI NPC.**

**Ngày:** 2026-08-26  
**Trạng thái:** Approved — Build  
**Lock:** Route top-level `/situations` (Compass 場面), hands-free opt-in (VAD high + barge-in toggle, push-to-talk fallback), hidden objectives 4 levels.

---

## 1. Kiến trúc

```
ScenarioGenerator (Location×Role×Task×Constraint×Difficulty×Props×Events + providers)
  ↓ NPCGenerator (role→ identity/behavior/speech register, per-session seed)
  ↓ GoalEngine (semantic intent+entity, graph NOT linear, hidden objectives)
  ↓ ScenarioStateMachine (generic ENTER→DISCOVER→REQUEST→CONFIRM→PAY→COMPLETE, chuyển khi intent+entity+conditions)
  ↓ ScenarioEventEngine (ITEM_UNAVAILABLE etc, allowed_states/cooldown/difficulty adaptive 0-1 beginner→2-4 expert)
  ↓ RecoveryEngine (clarify/confirm, skill not failure)
  ↓ Backend state (turn_id/state_version/event_id, idempotency, seed reproducible)
  ↓ Voice hands-free loop (NPC TTS→playback→VAD→record→STT→intent/entity/dialogue-act→state update→NPC TTS) reuse STTRouter/TTSRouter/AudioPlatform/VAD
  ↓ AI NPC (AIRouter structured {scenario, state, npc, goals, allowed_actions} → {speech, dialogue_act, state_action, emotion})
```

`apps/api/app/domains/situations/` (facade) reuse `Exercise/ExerciseAttempt(metrics_json.situational)/LearningItem` + `MasteryEngine` + `GameEventPublisher`.

---

## 2. Tích hợp Learning Engine

- Thêm `ExerciseType.SITUATIONAL_ROLEPLAY` (reuse `SCENARIO/ROLEPLAY` nếu đủ) + optional 2 variants, affinity `NATURALNESS/CONVERSATION`, `Exercise.extra_metadata.situational_config {location, user_role, actors[], goals[], constraints[], props{}, event_pool[], seed, difficulty{language,speed,social,event}}`.
- `ExerciseGenerator` mở `situational_overrides` → `AITask.SITUATIONAL_GENERATION`, `ExerciseEvaluator` delegate `SituationalEvaluator` (pragmatics register/keigo + pitch + intent) trước AI fallback.

---

## 3. Providers (replaceable)

- `LocationProvider` (food/transport/retail/healthcare/government/education/workplace/housing/social/travel → subtypes), `RoleProvider` (customer/clerk/server/manager/doctor/receptionist/taxi_driver/interviewer/landlord...), `TaskProvider` (purchase/order/complaint/schedule/...), `ConstraintProvider`, `EventProvider` (item unavailable/wrong order/fee/schedule change), `PropProvider` (menu/ticket map/form/invoice), `SpeechActProvider`, `RelationshipProvider` — nhỏ ontology, AI sinh instance.

---

## 4. NPC & Consistency

- `NPCGenerator` input role/location/relationship/difficulty/user_level → output `{identity{name,age_band,gender}, behavior{patience,directness,politeness,speech_speed}, speech{register,complexity,verbosity}}` per session, không persist global.
- `NPCSessionState` lưu name/role/personality/speech style/knowledge/emotion/memory `user_preferences/constraints/orders/facts` deterministic.

---

## 5. Voice Hands-Free

- Config `hands_free{vad_sensitivity, silence_timeout_ms 700-1400, auto_listen_delay, allow_barge_in, background_noise_mode}` adaptive `FAST 500-700/NORMAL 700-1000/PATIENT 1000-1400`, `VAD high 0.025/700ms`, `useAudioRecorder 16kHz` + `useAudioPlayer.playBase64`, barge-in stop TTS, backchannel `はい/うん` phân biệt `BACKCHANNEL vs ANSWER`.

---

## 6. API/Frontend

- Prefer `POST /learning/exercises/generate {situational_roleplay}` + `POST /learning/exercises/{id}/submit {situational_metrics}`, chỉ khi cần mới thêm `POST /situations/exercises/generate?sub_mode=situational_roleplay&pressure&duration&domain` + `POST /situations/exercises/{id}/submit` + `GET /situations/progress`, `POST /situations/session/{id}/turn` với `turn_id/state_version`.
- Frontend `app/situations/page.tsx` hybrid như `reflex`: discovery `Today's Practice/Recommended/Quick Survival/Business/Travel` từ `RecommendationEngine`, live `location+NPC+transcript+props+timer+goal progress`, hands-free opt-in toggle, `useSituationsSession` clone `useReflexSession` (phase IDLE/INTRO/NPC_SPEAKING/WAITING/USER_SPEAKING/TRANSCRIBING/RESOLVING/GENERATING/COMPLETED), `ScenarioProgress` + replay `seed`.

---

## 7. Verification

- Scenario generation property-based solvable, state machine deterministic, AI valid JSON + hallucination guard, voice silence/overlap/barge-in, task completion semantic (3 phrasings "生ビールください" đều pass ORDER_DRINK), no giant hardcoded DB.

**Sign-off:** Approved 2026-08-26 — Build A→G.
