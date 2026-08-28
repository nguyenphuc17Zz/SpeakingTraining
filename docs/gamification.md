# Gamification & RPG Engine

## 1. Core Principles & Ledger
- **Pedagogy First**: Gamification motivates practice but never compromises linguistic standards.
- **Immutable XP Ledger (`XPTransaction`)**: All XP awards are appended to an immutable transaction ledger (`uq_user_event_dedup`) to guarantee zero duplicate rewards.
- **Non-Linear Level Curve**: Level thresholds scale progressively ($XP = 100 \times \text{level}^{1.5}$) up to Master Samurai (Lv. 50).

---

## 2. Quests & Progression Systems
- **Daily & Weekly Quests**: Dynamically generated practice missions (e.g. *"Complete 3 conversation turns without particle errors"*, *"Shadow 5 YouTube segments"*).
- **Skill Tree**: Visual unlocking of fluency, naturalness, and grammar perks linked directly to actual `LearningItem` mastery.
- **Boss Battles**: High-stakes roleplay conversation challenges (e.g. *"Job Interview Boss"*, *"Izakaya Customer Service"*) with strict passing score thresholds and exclusive title rewards.
