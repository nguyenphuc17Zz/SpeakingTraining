# Phase 10 — RPG & Gamification Engine Architecture & Implementation Guide

## 1. Executive Summary & Core Philosophy

The **Phase 10 RPG & Gamification Engine** transforms Japanese speaking and pronunciation training into an engaging, high-motivation RPG game loop.

### Foundational Principle:
> **"Gamification absolutely must not compromise the integrity or objectivity of the Learning Engine."**

The Learning Engine remains the single source of truth for linguistic knowledge, mastery estimation, and adaptive curriculum. The Gamification Engine acts as a clean, decoupled consumer that observes **meaningful learning events** and translates genuine deliberate practice into transparent progression, levels, quests, achievements, and unlockable rewards.

```text
 ┌─────────────────────────────────────────────────────────────┐
 │              Core Learning & Audio Engines                  │
 │  (Phases 3-9: Conversation, Intelligence, Pronunciation,   │
 │   Learning Curriculum, Shadowing, Memory)                   │
 └──────────────────────────────┬──────────────────────────────┘
                                │ Emits Normalized Events
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                    GameEventPublisher                       │
 │              (Asynchronous / Non-Blocking Queue)            │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                   GameEventProcessor                        │
 │  - Idempotency Gate (Unique Event Key Audit)               │
 │  - Anti-Farming & Diminishing Returns Evaluation            │
 │  - Deterministic RewardPolicy Calculation                   │
 └──────┬───────────────────────┬───────────────────────┬──────┘
        │                       │                       │
        ▼                       ▼                       ▼
 ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
 │   XPService   │       │  QuestEngine  │       │  StreakService│
 │  (Immutable   │       │(Daily/Weekly) │       │(Timezone-Aware│
 │   XP Ledger)  │       └───────┬───────┘       │    Streaks)   │
 └──────┬────────┘               │               └───────────────┘
        │                        ▼
        │               ┌─────────────────┐
        │               │AchievementEngine│
        │               │(Declarative Trophies)
        │               └────────┬────────┘
        ▼                        ▼
 ┌─────────────────────────────────────────────────────────────┐
 │         GameProfile Cache & Prioritized Notifications       │
 └─────────────────────────────────────────────────────────────┘
```

---

## 2. Event-Driven Pipeline & Schema

### Normalized `GameEvent`
All learning events emitted across domains are standardized into the `GameEvent` contract with a deterministic SHA-256 idempotency key (`event_id`). Re-submitting the same event never awards duplicate XP.

| Event Type | Source Domain | Trigger Point | Payload Signals |
|---|---|---|---|
| `exercise.completed` | `learning` | `ExerciseSessionService.submit_exercise_attempt()` | score, difficulty, independence level, mastery delta |
| `conversation.completed` | `conversation` | `ConversationService.end_session()` | duration seconds, user turn count, mode |
| `pronunciation.attempted` | `pronunciation` | `PronunciationWorker.execute_job()` | overall score, acoustic interpretation, target type |
| `shadowing.completed` | `shadowing` | `ShadowingService.complete_segment_practice()` | timing score, accuracy, video segment ID |
| `learning_item.mastered` | `learning` | `LearningItemService.update_item_from_result()` | item key, lifecycle transition |
| `boss.cleared` | `gamification` | `BossService.submit_boss_result()` | boss key, pass score, title awarded |

---

## 3. Immutable XP Ledger Design

XP is stored as an **append-only ledger** in the `xp_transactions` table.
- Direct database updates to reduce XP are forbidden; corrections are made via explicit negative adjustment rows (`category="correction"`).
- The user's total balance is cached in `game_profiles.total_xp` for $O(1)$ query speed and reconciled against `SUM(xp_transactions.amount)`.

---

## 4. Mathematical Level Curve & Ranks

The RPG progression curve is governed by a polynomial formula:
$$\Delta \text{XP}(L) = \text{BASE\_XP} \cdot L^{1.15} + 50 \cdot L$$
- **Smooth Early Progression**: Level 1 $\to$ 2 requires 350 XP (~1 daily session).
- **Sustained Mid-Game**: Level 10 $\to$ 11 requires ~4,000 XP.
- **Meaningful Mastery**: Level 20 reaches *Samurai of Spoken Japanese (言霊の師範)*.

### Rank Tiers
1. **Beginner (初学者)**: Level 1 – 4
2. **Bronze (銅侍)**: Level 5 – 9
3. **Silver (銀侍)**: Level 10 – 19
4. **Gold (金侍)**: Level 20 – 34
5. **Platinum (白金達人)**: Level 35 – 49
6. **Diamond (金剛指南役)**: Level 50 – 69
7. **Master (伝説の師範)**: Level 70+

---

## 5. Anti-Farming & Diminishing Returns

To protect genuine deliberate practice and prevent spam without penalizing repetition:
- **Mastery updates always apply normally** in the Learning Engine.
- XP returns diminish on repeated identical drills within the same calendar day:
  - Attempt 1: 100% XP
  - Attempt 2: 70% XP
  - Attempt 3: 45% XP
  - Attempt 4: 25% XP
  - Attempt 5+: 10% XP (floor)
- Daily category soft caps limit repetitive grinding (e.g., 600 XP/day for repetitive drills).

---

## 6. Daily & Weekly Quest Engine

- Dynamically generates 3 personalized daily quests based on the learner's active goals and weak learning items:
  1. *Natural Conversation*: Speaking for $\ge 5$ minutes with an AI partner.
  2. *Target Practice*: Completing 2 interactive roleplay drills targeting priority weaknesses.
  3. *Pronunciation & Pitch*: Analyzing 2 pronunciation or YouTube shadowing clips.
- 2 Weekly marathon challenges reward consistent weekly practice.
- Progress is derived automatically from server-side `GameEvents`, preventing client-side spoofing.

---

## 7. Skill Tree Architecture

The Japanese Speaking Skill Tree spans 4 core competency branches:
1. **🗣 Fluency (流暢さ・瞬発力)**: Response Speed, Extended Turns, Filler Control.
2. **🌸 Naturalness (自然さ・敬語)**: Polite/Keigo Nuances, Casual Speech, Sentence Endings (ね/よ/わ).
3. **📜 Grammar (文法・助詞)**: Particle Control, Verb/Adjective Conjugations.
4. **🎯 Pronunciation (発音・音調)**: Mora Timing, Tokyo Pitch Accent Curves.

**Zero State Duplication**: Node masteries $[0.0 - 1.0]$ are calculated dynamically by aggregating `LearningItem.overall_mastery` and attempt histories from Phase 7.

---

## 8. High-Stakes Boss Battle Arena

Boss Battles represent conversational challenge gauntlets:
- **Japanese Job Interview (面接官の試練)**: Formal keigo scenario under pressure (Pass Score: 75.0 pts).
- **Difficult Client Complaint (顧客クレーム対応)**: Diplomatic problem-solving & crisis de-escalation (Pass Score: 80.0 pts).
- **Live Debate (白熱の意見討論会)**: Spontaneous argumentative dialogue (Pass Score: 85.0 pts).

Bosses reuse the existing Conversation and Exercise evaluation engines. First victory awards massive XP and exclusive equipable titles; repeat attempts yield reduced replay rewards. Failure never resets streaks.

---

## 9. Timezone-Aware Streaks

- Streaks are calculated using the learner's configured timezone (`user.timezone` or `UserSettings.timezone`).
- Practicing at 23:55 in Tokyo correctly counts for that day regardless of server UTC time.
- Integrated **Streak Freezes** protect learners from losing streaks during unavoidable off-days.

---

## 10. Web User Interface

- `/game`: Central RPG Dojo Hub with live XP progress, streak card, daily quests, and quick links.
- `/quests`: Daily & weekly missions tab with progress rings and XP badges.
- `/achievements`: Trophy gallery categorized by rarity (Common, Rare, Epic, Legendary).
- `/skills`: Interactive 4-branch Skill Tree with node inspection and direct training links.
- `/bosses`: Boss Arena challenge cards with difficulty tiers, pass benchmarks, and battle launcher.
- `/unlocks`: Progression rewards gallery for equipping titles and custom personas.
- Global non-blocking `RewardToast` celebration overlay on all pages.

---

## 11. Economy Balance Simulation Results

Simulated over 30 and 90-day learning trajectories (`scripts/simulate_game_progression.py`):

| Profile | Routine | 30-Day XP | 30-Day Level & Rank | 90-Day XP | 90-Day Level & Rank |
|---|---|---|---|---|---|
| **Casual** | 10 min/day (1 drill) | 1,800 | Lv. 3 (Beginner) | 5,400 | Lv. 5 (Bronze) |
| **Consistent** | 30 min/day (Roleplay + Pronunciation + Quests) | 19,050 | Lv. 9 (Bronze) | 57,150 | Lv. 16 (Silver) |
| **Hardcore** | 60 min/day (Full conversation + 3 drills + Boss) | 26,270 | Lv. 11 (Silver) | 78,810 | Lv. 18 (Silver) |
| **Irregular** | 3 days/week | 8,255 | Lv. 6 (Bronze) | 24,765 | Lv. 11 (Silver) |
