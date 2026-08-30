"""Unit test for Conversation Turn Scaffolding (suggestions & key vocab)."""

import pytest
from app.domains.conversation.service import ConversationService
from app.domains.personas.models import Persona


def test_conversation_fallback_scaffolding():
    """Verify that _generate_fallback_scaffolding generates rich suggestions and key vocab."""
    svc = ConversationService(None)  # Session not needed for pure logic

    persona = Persona(name="Yamada", role="Business Boss", personality="Strict", speaking_style="Formal Keigo")

    # 1. Work context
    work_scaffold = svc._generate_fallback_scaffolding("来週のプレゼンの準備はどうなっていますか？", persona=persona)
    assert "suggestions" in work_scaffold
    assert len(work_scaffold["suggestions"]) >= 2
    assert "key_vocab" in work_scaffold
    assert len(work_scaffold["key_vocab"]) >= 2

    # 2. Restaurant / Food context
    food_scaffold = svc._generate_fallback_scaffolding("ご注文はお決まりでしょうか？何にいたしましょうか？", persona=persona)
    assert any("注文" in v["ja"] or "おすすめ" in v["ja"] for v in food_scaffold["key_vocab"])

    # 3. General conversation
    gen_scaffold = svc._generate_fallback_scaffolding("今日はいい天気ですね！", persona=persona)
    assert len(gen_scaffold["suggestions"]) >= 2
