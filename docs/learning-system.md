# Learning Engine & Adaptive Curriculum

## 1. Domain Architecture
The **Learning Engine** turns conversation and pronunciation evidence into targeted, daily practice routines:
- **`LearningItem`**: Granular Japanese linguistic targets (Grammar patterns, vocabulary, particles, pitch accents) with persistent mastery levels $[0.0, 1.0]$.
- **`LearningPlan`**: Daily personalized study schedule generated per user calendar day based on time budget (15, 30, or 45 mins).
- **`Exercise` & `ExerciseAttempt`**: 5 core archetypes:
  1. *Targeted Drill* (Fix specific recurring error)
  2. *Conversation Scenario* (Role-play in target domain)
  3. *Pronunciation & Pitch Focus* (Mora rhythm and pitch accent)
  4. *Spaced Repetition Review* (SM-2 review of near-decay items)
  5. *Exploratory Challenge* (New JLPT level expansion)

---

## 2. Spaced Repetition & Mastery Delta
Mastery is updated deterministically from exercise performance:
$$\Delta \text{Mastery} = f(\text{score}, \text{independence\_level}, \text{response\_speed\_ms})$$
- Independent success without hints boosts mastery by $+0.15$.
- Scaffolded or retry attempts adjust by $+0.05$.
- Unsuccessful attempts schedule spaced repetition review within 24–48 hours.
