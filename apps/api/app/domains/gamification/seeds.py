from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.gamification.models import (
    AchievementDefinition,
    BossDefinition,
    SkillNodeDefinition,
    UnlockableDefinition,
)


class GamificationSeeder:
    """
    Seeds initial system achievement definitions, skill tree layout, boss battle challenges, and unlockables.
    """

    @classmethod
    async def seed_defaults(cls, db: AsyncSession) -> None:
        await cls._seed_achievements(db)
        await cls._seed_skill_nodes(db)
        await cls._seed_bosses(db)
        await cls._seed_unlockables(db)

    @classmethod
    async def _seed_achievements(cls, db: AsyncSession) -> None:
        achievements_data = [
            {
                "key": "first_conversation",
                "title": "First Step (最初の一歩)",
                "description": "Complete your first spoken Japanese conversation session.",
                "rarity": "common",
                "category": "conversation",
                "icon": "message-circle",
                "condition_type": "conversation_count",
                "target_value": 1.0,
                "xp_reward": 100,
            },
            {
                "key": "streak_7d",
                "title": "7-Day Flame (7日間の闘志)",
                "description": "Maintain a continuous 7-day meaningful learning streak.",
                "rarity": "rare",
                "category": "streak",
                "icon": "flame",
                "condition_type": "streak_days",
                "target_value": 7.0,
                "xp_reward": 300,
            },
            {
                "key": "streak_30d",
                "title": "30-Day Dedication (30日継続の証)",
                "description": "Maintain a continuous 30-day speaking streak.",
                "rarity": "epic",
                "category": "streak",
                "icon": "zap",
                "condition_type": "streak_days",
                "target_value": 30.0,
                "xp_reward": 1000,
            },
            {
                "key": "pitch_apprentice",
                "title": "Pitch Explorer (音調の探求者)",
                "description": "Complete 15 pronunciation or pitch accent practice attempts.",
                "rarity": "rare",
                "category": "pronunciation",
                "icon": "mic",
                "condition_type": "pronunciation_count",
                "target_value": 15.0,
                "xp_reward": 250,
            },
            {
                "key": "shadowing_adept",
                "title": "Shadowing Master (シャドーイング達人)",
                "description": "Shadow 30 sentence segments from native Japanese YouTube clips.",
                "rarity": "epic",
                "category": "shadowing",
                "icon": "play-circle",
                "condition_type": "shadowing_count",
                "target_value": 30.0,
                "xp_reward": 500,
            },
            {
                "key": "mastery_vanguard",
                "title": "Mastery Scholar (知識の定着)",
                "description": "Master 5 recurring grammar, particle, or vocabulary weaknesses.",
                "rarity": "epic",
                "category": "mastery",
                "icon": "award",
                "condition_type": "mastered_items_count",
                "target_value": 5.0,
                "xp_reward": 450,
            },
            {
                "key": "boss_conqueror",
                "title": "Boss Conqueror (強敵撃破)",
                "description": "Successfully clear your first Japanese Boss Battle conversational challenge.",
                "rarity": "legendary",
                "category": "boss",
                "icon": "swords",
                "condition_type": "boss_cleared_count",
                "target_value": 1.0,
                "xp_reward": 800,
            },
        ]

        for d in achievements_data:
            stmt = select(AchievementDefinition).where(AchievementDefinition.key == d["key"])
            res = await db.execute(stmt)
            if not res.scalar_one_or_none():
                ach = AchievementDefinition(**d)
                db.add(ach)

        await db.commit()

    @classmethod
    async def _seed_skill_nodes(cls, db: AsyncSession) -> None:
        skill_nodes_data = [
            # Fluency Branch
            {
                "key": "fluency_response_speed",
                "name": "Response Speed (瞬発力)",
                "description": "Deliver spontaneous Japanese answers within 2 seconds without hesitation.",
                "category": "fluency",
                "icon": "zap",
                "prerequisites_json": [],
                "linked_item_types_json": ["fluency"],
                "display_order": 1,
            },
            {
                "key": "fluency_long_response",
                "name": "Extended Turns (長文展開力)",
                "description": "Speak in coherent multi-sentence paragraphs using conjunctions.",
                "category": "fluency",
                "icon": "message-square",
                "prerequisites_json": ["fluency_response_speed"],
                "linked_item_types_json": ["fluency", "sentence_pattern"],
                "display_order": 2,
            },
            {
                "key": "fluency_fillers",
                "name": "Filler Word Mastery (フィラー制御)",
                "description": "Minimize unnatural pauses and use natural fillers like ええと, あの.",
                "category": "fluency",
                "icon": "volume-2",
                "prerequisites_json": ["fluency_response_speed"],
                "linked_item_types_json": ["filler"],
                "display_order": 3,
            },
            # Naturalness Branch
            {
                "key": "natural_polite_keigo",
                "name": "Polite & Keigo (丁寧語・敬語)",
                "description": "Master desu/masu, sonkeigo, and kenjougo in professional situations.",
                "category": "naturalness",
                "icon": "shield",
                "prerequisites_json": [],
                "linked_item_types_json": ["politeness"],
                "display_order": 4,
            },
            {
                "key": "natural_casual_speech",
                "name": "Casual Nuances (タメ口・日常表現)",
                "description": "Use natural plain-form, contractions, and friendly conversational tone.",
                "category": "naturalness",
                "icon": "smile",
                "prerequisites_json": [],
                "linked_item_types_json": ["naturalness", "word_choice"],
                "display_order": 5,
            },
            {
                "key": "natural_sentence_endings",
                "name": "Sentence Endings (終助詞: ね/よ/よね)",
                "description": "Accurately convey sentiment and empathy using nuanced Japanese ending particles.",
                "category": "naturalness",
                "icon": "feather",
                "prerequisites_json": ["natural_casual_speech"],
                "linked_item_types_json": ["particle", "naturalness"],
                "display_order": 6,
            },
            # Grammar Branch
            {
                "key": "grammar_particles",
                "name": "Particle Precision (助詞の完全制御)",
                "description": "Master nuanced particles like は vs が, に vs で, and を.",
                "category": "grammar",
                "icon": "link",
                "prerequisites_json": [],
                "linked_item_types_json": ["particle"],
                "display_order": 7,
            },
            {
                "key": "grammar_conjugations",
                "name": "Verb & Adj Conjugations (活用変化)",
                "description": "Seamlessly conjugate conditional (〜たら, 〜ば), passive, and causative verbs.",
                "category": "grammar",
                "icon": "refresh-cw",
                "prerequisites_json": ["grammar_particles"],
                "linked_item_types_json": ["conjugation", "grammar"],
                "display_order": 8,
            },
            # Pronunciation Branch
            {
                "key": "pron_mora_timing",
                "name": "Mora Rhythm & Timing (モーラ拍感覚)",
                "description": "Perfect small tsu (促音), long vowels (長音), and nasal N (撥音) durations.",
                "category": "pronunciation",
                "icon": "activity",
                "prerequisites_json": [],
                "linked_item_types_json": ["pronunciation"],
                "display_order": 9,
            },
            {
                "key": "pron_pitch_accent",
                "name": "Pitch Accent Curves (高低アクセント)",
                "description": "Master Japanese Tokyo pitch accent patterns (Heiban, Atamadaka, Nakadaka).",
                "category": "pronunciation",
                "icon": "trending-up",
                "prerequisites_json": ["pron_mora_timing"],
                "linked_item_types_json": ["pitch_accent", "pronunciation"],
                "display_order": 10,
            },
        ]

        for s in skill_nodes_data:
            stmt = select(SkillNodeDefinition).where(SkillNodeDefinition.key == s["key"])
            res = await db.execute(stmt)
            if not res.scalar_one_or_none():
                node = SkillNodeDefinition(**s)
                db.add(node)

        await db.commit()

    @classmethod
    async def _seed_bosses(cls, db: AsyncSession) -> None:
        bosses_data = [
            {
                "key": "boss_interview",
                "name": "Japanese Job Interview (面接官の試練)",
                "subtitle": "High-pressure formal workplace scenario",
                "description": "Answer complex job interview questions in polite keigo and explain your strengths convincingly.",
                "persona_key": "system_default_persona",
                "difficulty": "normal",
                "required_level": 3,
                "pass_score_threshold": 75.0,
                "xp_reward": 500,
                "title_reward": "Interview Ready (面接突破)",
                "objectives_json": [
                    "Use polite teinei/keigo speech forms consistently",
                    "Provide clear structured answers with reasons",
                    "Maintain steady response tempo without abandoning sentences",
                ],
                "scenario_template": "You are interviewing for a software development position in Tokyo. The interviewer is asking about your past projects and teamwork.",
            },
            {
                "key": "boss_difficult_client",
                "name": "Angry Customer Complaint (顧客クレーム対応)",
                "subtitle": "Crisis negotiation & diplomatic problem solving",
                "description": "Calm an upset Japanese client politely while explaining the delay and proposing an actionable solution.",
                "persona_key": "system_default_persona",
                "difficulty": "hard",
                "required_level": 8,
                "pass_score_threshold": 80.0,
                "xp_reward": 850,
                "title_reward": "Crisis Negotiator (折衝の名手)",
                "objectives_json": [
                    "Express sincere apology using sonkeigo/kenjougo",
                    "De-escalate tension without defensive wording",
                    "Propose a concrete solution clearly",
                ],
                "scenario_template": "A major client has received an incorrect shipment delivery. You must listen, apologize formally, and resolve the matter.",
            },
            {
                "key": "boss_japanese_debate",
                "name": "Live Topic Debate (白熱の意見討論会)",
                "subtitle": "Fast-paced philosophical exchange",
                "description": "Engage in a live debate regarding remote work versus office culture. Present evidence and respectfully counter-argue.",
                "persona_key": "system_default_persona",
                "difficulty": "extreme",
                "required_level": 15,
                "pass_score_threshold": 85.0,
                "xp_reward": 1200,
                "title_reward": "Debate Champion (論客の極み)",
                "objectives_json": [
                    "State opinion with 〜と思う / 〜と考えております",
                    "Use polite disagreement structures (〜という側面もありますが)",
                    "Maintain natural native conversational rhythm",
                ],
                "scenario_template": "You are participating in a panel discussion regarding the future of work culture in Japan.",
            },
        ]

        for b in bosses_data:
            stmt = select(BossDefinition).where(BossDefinition.key == b["key"])
            res = await db.execute(stmt)
            if not res.scalar_one_or_none():
                boss = BossDefinition(**b)
                db.add(boss)

        await db.commit()

    @classmethod
    async def _seed_unlockables(cls, db: AsyncSession) -> None:
        unlockables_data = [
            {
                "key": "title_apprentice",
                "unlock_type": "title",
                "title": "Junior Samurai (見習い侍)",
                "description": "Badge of honor for embarking on the spoken Japanese path.",
                "level_required": 1,
                "asset_reference": "badge-apprentice",
            },
            {
                "key": "title_conversation_adept",
                "unlock_type": "title",
                "title": "Conversationalist (談話の名手)",
                "description": "Proof of reaching Level 5 in natural spoken exchanges.",
                "level_required": 5,
                "asset_reference": "badge-adept",
            },
            {
                "key": "title_pitch_hunter",
                "unlock_type": "title",
                "title": "Pitch Accent Hunter (音調の狩人)",
                "description": "Awarded at Level 10 for relentless acoustic practice.",
                "level_required": 10,
                "asset_reference": "badge-pitch",
            },
            {
                "key": "title_grandmaster",
                "unlock_type": "title",
                "title": "Speaking Grandmaster (言霊の師範)",
                "description": "Elite distinction for Level 20 Japanese fluency.",
                "level_required": 20,
                "asset_reference": "badge-master",
            },
        ]

        for u in unlockables_data:
            stmt = select(UnlockableDefinition).where(UnlockableDefinition.key == u["key"])
            res = await db.execute(stmt)
            if not res.scalar_one_or_none():
                unl = UnlockableDefinition(**u)
                db.add(unl)

        await db.commit()
        logger.info("[GamificationSeeder] Seeded default gamification definitions successfully.")
