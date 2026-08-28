from app.domains.conversation.prompts import ConversationPromptBuilder
from app.domains.personas.models import Persona


def test_conversation_prompt_builder_structure():
    persona = Persona(
        name="Takeshi",
        role="Friendly Senpai",
        personality="Warm, encouraging, natural conversationalist",
        speaking_style="Casual Tameguchi",
        difficulty="N3",
        is_system=True,
    )

    prompt = ConversationPromptBuilder.build_system_prompt(persona, mode="conversation")

    assert "Takeshi" in prompt
    assert "Friendly Senpai" in prompt
    assert "Casual Tameguchi" in prompt
    assert "N3" in prompt
    assert "CONVERSATION MODE ACTIVE" in prompt
    assert "Spoken Japanese Cadence" in prompt


def test_coaching_mode_prompt_includes_hint_instruction():
    persona = Persona(
        name="Sakura Sensei",
        role="Japanese Teacher",
        personality="Patient, polite educator",
        speaking_style="Polite Desu/Masu",
        difficulty="N4",
        is_system=True,
    )

    prompt = ConversationPromptBuilder.build_system_prompt(persona, mode="coaching")

    assert "COACHING MODE ACTIVE" in prompt
    assert "---HINT---" in prompt
    assert "💡 Better:" in prompt
