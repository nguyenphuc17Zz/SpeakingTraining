from app.core.logging import logger
from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask
from app.domains.conversation.models import ConversationSession, ConversationTurn
from app.domains.conversation.prompts import ConversationPromptBuilder
from app.domains.personas.models import Persona


class ContextBudgetManager:
    """
    Calculates dynamic token and character budgets for real-time conversation turns.
    Prevents token bloat, keeps latency low, and ensures critical instructions are preserved.
    """

    MAX_LEARNER_CONTEXT_CHARS: int = 800
    MAX_CONVERSATION_HISTORY_CHARS: int = 3500  # Approx ~1400 tokens

    @classmethod
    def trim_learner_context(cls, learner_context: str | None) -> str | None:
        if not learner_context:
            return None
        if len(learner_context) <= cls.MAX_LEARNER_CONTEXT_CHARS:
            return learner_context
        logger.debug(f"[ContextBudgetManager] Trimming learner context from {len(learner_context)} to {cls.MAX_LEARNER_CONTEXT_CHARS} chars.")
        return learner_context[: cls.MAX_LEARNER_CONTEXT_CHARS] + "\n...</learner_memory>"

    @classmethod
    def select_budgeted_turns(
        cls,
        turns_history: list[ConversationTurn],
        max_turns: int = 12,
    ) -> list[ConversationTurn]:
        """Selects the most recent turns that fit within both turn count and character budget."""
        if not turns_history:
            return []

        # Start with at most max_turns
        candidates = turns_history[-max_turns:] if len(turns_history) > max_turns else list(turns_history)

        # Ensure total characters do not exceed budget
        total_chars = sum(len(t.transcript or "") for t in candidates)
        while len(candidates) > 4 and total_chars > cls.MAX_CONVERSATION_HISTORY_CHARS:
            removed = candidates.pop(0)
            total_chars -= len(removed.transcript or "")

        return candidates


class ConversationContextBuilder:
    """Constructs normalized AIRequest payloads from session state, persona prompts, and turn history."""

    def __init__(self, max_history_turns: int = 12):
        self.max_history_turns = max_history_turns

    def build_ai_request(
        self,
        session: ConversationSession,
        persona: Persona,
        current_user_text: str,
        turns_history: list[ConversationTurn],
        user_id: str,
        learner_context: str | None = None,
    ) -> AIRequest:
        """Builds a budget-aware AIRequest ready for AIRouter."""
        # 1. Build System Instruction with guarded learner context
        system_prompt = ConversationPromptBuilder.build_system_prompt(
            persona=persona,
            mode=session.mode,
        )

        guarded_learner_ctx = ContextBudgetManager.trim_learner_context(learner_context)
        if guarded_learner_ctx:
            system_prompt = f"{system_prompt}\n\n{guarded_learner_ctx}"

        messages: list[AIMessage] = [
            AIMessage(role=AIMessageRole.SYSTEM, content=system_prompt)
        ]

        # 2. Window & Budget Management: Select budgeted turns
        active_history = ContextBudgetManager.select_budgeted_turns(
            turns_history,
            max_turns=self.max_history_turns,
        )

        # 3. Add chronological turns
        for turn in active_history:
            role = AIMessageRole.USER if turn.speaker == "user" else AIMessageRole.ASSISTANT
            # Strip out hint delimiter if present in raw assistant turn text so AI doesn't see hint format in context
            content = (turn.transcript or "").split("---HINT---")[0].strip()
            if content:
                messages.append(AIMessage(role=role, content=content))

        # 4. Add current user utterance
        messages.append(AIMessage(role=AIMessageRole.USER, content=current_user_text.strip()))

        # 5. Build AIRequest
        return AIRequest(
            task=AITask.CONVERSATION,
            messages=messages,
            provider=session.provider_preference,
            model=session.model_preference,
            temperature=0.7,
            max_output_tokens=250,  # Spoken brevity constraint
            system_instruction=system_prompt,
            user_id=user_id,
        )


class ConversationContextManager:
    """Manages short-term conversation context and history truncation."""

    def __init__(self, context_builder: ConversationContextBuilder | None = None):
        self.builder = context_builder or ConversationContextBuilder()

    def create_request(
        self,
        session: ConversationSession,
        persona: Persona,
        current_user_text: str,
        turns_history: list[ConversationTurn],
        user_id: str,
        learner_context: str | None = None,
    ) -> AIRequest:
        return self.builder.build_ai_request(
            session=session,
            persona=persona,
            current_user_text=current_user_text,
            turns_history=turns_history,
            user_id=user_id,
            learner_context=learner_context,
        )
