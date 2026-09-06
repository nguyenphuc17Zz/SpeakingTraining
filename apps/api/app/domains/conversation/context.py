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
    def _extract_shingle_tokens(cls, text: str) -> set[str]:
        """Extracts character bi-grams and words from text for TextRank graph construction."""
        if not text:
            return set()
        import re

        clean = re.sub(r"[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", "", text.lower())
        tokens: set[str] = set()
        # Words (whitespace/latin)
        words = [w for w in clean.split() if len(w) > 1]
        tokens.update(words)
        # Bi-grams for continuous Japanese script
        chars = [c for c in clean if not c.isspace()]
        for i in range(len(chars) - 1):
            tokens.add(chars[i] + chars[i + 1])
        return tokens

    @classmethod
    def compute_turn_salience(cls, turns: list[ConversationTurn]) -> dict[int, float]:
        """Computes TextRank graph salience score for each turn.

        Builds a co-occurrence similarity graph between turns and applies PageRank iteration.
        """
        import math

        n = len(turns)
        if n == 0:
            return {}
        if n == 1:
            return {0: 1.0}

        token_sets = [cls._extract_shingle_tokens(t.transcript or "") for t in turns]

        # Build adjacency matrix with Mihalcea-Tarau BM25-normalized weight
        weights = [[0.0] * n for _ in range(n)]
        row_sums = [0.0] * n
        for i in range(n):
            for j in range(i + 1, n):
                common = len(token_sets[i] & token_sets[j])
                if common > 0:
                    denom = math.log(1 + len(token_sets[i])) + math.log(1 + len(token_sets[j]))
                    w = common / max(0.1, denom)
                    weights[i][j] = w
                    weights[j][i] = w
                    row_sums[i] += w
                    row_sums[j] += w

        # PageRank iteration
        d = 0.85
        scores = [1.0] * n
        max_iter = 25
        tol = 1e-4

        for _ in range(max_iter):
            next_scores = [1.0 - d] * n
            for i in range(n):
                for j in range(n):
                    if i != j and weights[j][i] > 0 and row_sums[j] > 0:
                        next_scores[i] += d * (weights[j][i] / row_sums[j]) * scores[j]
            diff = sum(abs(next_scores[i] - scores[i]) for i in range(n))
            scores = next_scores
            if diff < tol:
                break

        return {i: scores[i] for i in range(n)}

    @classmethod
    def select_budgeted_turns(
        cls,
        turns_history: list[ConversationTurn],
        max_turns: int = 12,
        preserve_premise: bool = False,
    ) -> list[ConversationTurn]:
        """Selects budgeted turns using TextRank Graph Salience and Priority Knapsack.

        - If preserve_premise is True: preserves first 2 premise turns + last 3 recent turns,
          and fills middle budget with highest TextRank salience turns.
        - If preserve_premise is False: focuses on the recent max_turns window, and uses TextRank
          salience to prune lowest-value turns if character budget is exceeded.
        - Result is strictly sorted chronologically.
        """
        if not turns_history:
            return []

        if preserve_premise and len(turns_history) > 5:
            n = len(turns_history)
            start_indices = [0, 1]
            end_indices = [n - 3, n - 2, n - 1]
            middle_indices = list(range(2, n - 3))

            start_turns = [turns_history[i] for i in start_indices]
            end_turns = [turns_history[i] for i in end_indices]
            middle_turns = [turns_history[i] for i in middle_indices]

            anchor_chars = sum(len(t.transcript or "") for t in start_turns + end_turns)
            remaining_budget = max(0, cls.MAX_CONVERSATION_HISTORY_CHARS - anchor_chars)
            max_middle_turns = max(0, max_turns - len(start_indices) - len(end_indices))

            if not middle_turns or max_middle_turns == 0 or remaining_budget == 0:
                selected_indices = sorted(start_indices + end_indices)
                return [turns_history[i] for i in selected_indices]

            middle_salience = cls.compute_turn_salience(middle_turns)
            scored_candidates: list[tuple[int, float, int]] = []
            for local_idx, turn in enumerate(middle_turns):
                score = middle_salience.get(local_idx, 1.0)
                length = max(10, len(turn.transcript or ""))
                density = score / length
                global_idx = middle_indices[local_idx]
                scored_candidates.append((global_idx, density, length))

            scored_candidates.sort(key=lambda x: x[1], reverse=True)

            chosen_middle_indices: list[int] = []
            accumulated_chars = 0
            for g_idx, _density, length in scored_candidates:
                if len(chosen_middle_indices) >= max_middle_turns:
                    break
                if accumulated_chars + length <= remaining_budget:
                    chosen_middle_indices.append(g_idx)
                    accumulated_chars += length

            all_selected_indices = sorted(start_indices + chosen_middle_indices + end_indices)
            return [turns_history[i] for i in all_selected_indices]

        # Standard recency window
        candidates = turns_history[-max_turns:] if len(turns_history) > max_turns else list(turns_history)
        total_chars = sum(len(t.transcript or "") for t in candidates)

        if total_chars <= cls.MAX_CONVERSATION_HISTORY_CHARS:
            return candidates

        # If characters exceed budget, apply TextRank salience knapsack to prune lowest-salience turns
        # Anchor the most recent 2-3 turns
        if len(candidates) <= 3:
            return candidates

        m = len(candidates)
        recent_anchor_count = min(3, m)
        recents = candidates[-recent_anchor_count:]
        prunable = candidates[:-recent_anchor_count]

        recent_chars = sum(len(t.transcript or "") for t in recents)
        avail_budget = max(0, cls.MAX_CONVERSATION_HISTORY_CHARS - recent_chars)

        salience_map = cls.compute_turn_salience(prunable)
        scored_prunable: list[tuple[int, float, int]] = []
        for idx, turn in enumerate(prunable):
            score = salience_map.get(idx, 1.0)
            length = max(10, len(turn.transcript or ""))
            density = score / length
            scored_prunable.append((idx, density, length))

        # Sort by density descending (highest value per char kept)
        scored_prunable.sort(key=lambda x: x[1], reverse=True)

        chosen_indices: list[int] = []
        used_chars = 0
        for idx, _density, length in scored_prunable:
            if used_chars + length <= avail_budget:
                chosen_indices.append(idx)
                used_chars += length

        chosen_indices.sort()
        selected = [prunable[i] for i in chosen_indices] + recents
        return selected


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
