from app.domains.ai.contracts import AIMessageRole, AITask
from app.domains.conversation.context import ConversationContextBuilder
from app.domains.conversation.models import ConversationSession, ConversationTurn
from app.domains.personas.models import Persona


def test_conversation_context_builder_window_trimming():
    persona = Persona(
        name="Takeshi",
        role="Friendly Senpai",
        personality="Warm and encouraging",
        speaking_style="Casual Tameguchi",
        difficulty="N3",
        is_system=True,
    )

    session = ConversationSession(
        user_id="user-1",
        persona_id=persona.id,
        mode="conversation",
        status="active",
        provider_preference="gemini",
        model_preference="gemini-1.5-flash",
    )

    # Generate 16 past turns (8 user, 8 assistant)
    turns = []
    for i in range(16):
        speaker = "user" if i % 2 == 0 else "assistant"
        turns.append(
            ConversationTurn(
                session_id=session.id,
                sequence=i + 1,
                speaker=speaker,
                transcript=f"Turn message {i + 1}",
            )
        )

    builder = ConversationContextBuilder(max_history_turns=6)
    ai_request = builder.build_ai_request(
        session=session,
        persona=persona,
        current_user_text="最新のメッセージです。",
        turns_history=turns,
        user_id="user-1",
    )

    assert ai_request.task == AITask.CONVERSATION
    assert ai_request.provider == "gemini"
    assert ai_request.model == "gemini-1.5-flash"

    # Index 0 is system message
    assert ai_request.messages[0].role == AIMessageRole.SYSTEM
    assert "Takeshi" in ai_request.messages[0].content

    # Max history is 6 turns + 1 system prompt + 1 current message = 8 messages total
    assert len(ai_request.messages) == 8

    # Oldest turn included should be Turn 11 (the 11th turn)
    assert "Turn message 11" in ai_request.messages[1].content
    # Last message should be the current user text
    assert ai_request.messages[-1].content == "最新のメッセージです。"
    assert ai_request.messages[-1].role == AIMessageRole.USER
