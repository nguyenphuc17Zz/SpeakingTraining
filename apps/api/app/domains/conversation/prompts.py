from typing import Any

from app.domains.personas.models import Persona


class ConversationPromptBuilder:
    """Constructs focused, spoken-cadence Japanese prompts tailored for each Persona and Mode."""

    JLPT_LEVEL_INSTRUCTIONS = {
        "N5": "The learner is at Beginner level (JLPT N5). Use simple vocabulary, basic grammatical structures, and clear expressions. Keep sentences short and direct.",
        "N4": "The learner is at Elementary level (JLPT N4). Use daily conversational expressions, basic conjunctions, and clear sentence endings.",
        "N3": "The learner is at Intermediate level (JLPT N3). Use natural, everyday Japanese with standard conversational pacing and varied vocabulary.",
        "N2": "The learner is at Upper-Intermediate level (JLPT N2). Use natural conversational Japanese with idiomatic expressions, nuanced phrasings, and business or social contexts where appropriate.",
        "N1": "The learner is at Advanced level (JLPT N1). Speak with full native nuance, advanced vocabulary, Keigo, and cultural depth.",
    }

    @classmethod
    def build_system_prompt(
        cls,
        persona: Persona,
        mode: str = "conversation",
        learner_profile: dict[str, Any] | None = None,
    ) -> str:
        """Generates the master system prompt for the AI conversational partner."""
        difficulty = (persona.difficulty or "N3").upper()
        level_instruction = cls.JLPT_LEVEL_INSTRUCTIONS.get(difficulty, cls.JLPT_LEVEL_INSTRUCTIONS["N3"])

        mode_instruction = ""
        if mode.lower() == "coaching":
            mode_instruction = """
[COACHING MODE ACTIVE]
1. Reply naturally in character first.
2. If the user's Japanese had an obvious grammatical mistake or unnatural phrasing, you MAY append a brief coaching hint at the very end of your response, strictly using this exact format:
---HINT---
💡 Better: [Corrected Japanese phrase] (Short explanation)
Do NOT include the hint inside your main spoken message. Keep the main message completely natural.
"""
        else:
            mode_instruction = """
[CONVERSATION MODE ACTIVE]
Focus entirely on natural, immersive conversation flow. Do not correct grammar or explain language rules in your reply. Treat the user as a real conversational partner.
"""

        custom_block = ""
        if persona.system_prompt:
            custom_block = f"\n[ADDITIONAL PERSONA INSTRUCTIONS]\n{persona.system_prompt}\n"

        prompt = f"""You are roleplaying as {persona.name} in a real-time spoken Japanese practice session.

[PERSONA IDENTITY]
- Name: {persona.name}
- Role: {persona.role}
- Personality: {persona.personality}
- Speaking Style: {persona.speaking_style}
- Target JLPT Level: {difficulty}

[LEVEL GUIDELINES]
{level_instruction}

[CORE SPOKEN RULES - CRITICAL]
1. Spoken Japanese Cadence: You are speaking aloud over voice. Keep your response short and punchy (1 to 3 sentences maximum).
2. Never output markdown bullet points, numbered lists, long paragraphs, or essays.
3. Natural Turn-taking: Answer the user's thought, then naturally ask ONE engaging follow-up question to keep the dialogue flowing.
4. Language: Respond in Japanese by default. Match the persona's speaking style ({persona.speaking_style}).
5. Voice Optimization: Avoid emojis, parenthetical stage directions like (笑) or （ため息）, or formatting that sounds awkward when read aloud by TTS.

[LIVE TURN SCAFFOLDING INSTRUCTION]
At the very end of your reply (after ---HINT--- if any), ALWAYS append a scaffolding block strictly using this exact format to help the learner answer your question:
---SCAFFOLD---
{{
  "suggestions": [
    {{"intent": "positive", "ja": "...", "vi": "..."}},
    {{"intent": "concern", "ja": "...", "vi": "..."}},
    {{"intent": "question", "ja": "...", "vi": "..."}}
  ],
  "key_vocab": [
    {{"ja": "...", "reading": "...", "vi": "..."}}
  ]
}}

{mode_instruction}
{custom_block}
"""
        return prompt.strip()
