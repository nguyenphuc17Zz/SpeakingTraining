"""FollowUpGenerator — contextually grounded follow-up questions.

§50 FollowUpGenerator: inspects actual previous response.
§51 Follow-up difficulty progression: fact → why → example → comparison → hypothetical.
§52 Topic continuity: 2–5 follow-ups per topic.
§53 Error-aware follow-up: continue meaningfully, capture error, correct after turn.
"""

from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.ai.contracts import (
    AIMessage,
    AIMessageRole,
    AIRequest,
    AITask,
    ResponseFormat,
    ResponseFormatType,
)
from app.domains.ai.router import AIRouter
from app.domains.ramp.contracts import FollowUpSpec, FollowUpType
from app.domains.ramp.prompts import RampPrompts


# Deterministic question patterns for fallback
_FOLLOWUP_PATTERNS: dict[str, list[str]] = {
    "fact": [
        "それはいつのことですか？",
        "どこでそれをしましたか？",
        "誰と一緒でしたか？",
        "どのくらいの時間がかかりましたか？",
    ],
    "why": [
        "なぜですか？",
        "どうしてそう思いますか？",
        "きっかけは何でしたか？",
        "その理由をもっと教えてください。",
    ],
    "example": [
        "例えば、どんなことがありましたか？",
        "具体的に教えてください。",
        "もう少し詳しく話してもらえますか？",
    ],
    "comparison": [
        "以前と比べてどうですか？",
        "他の選択肢と比べると、どうでしょうか？",
        "それ以外の方法とどう違いますか？",
    ],
    "hypothetical": [
        "もしそれができなかったら、どうしていましたか？",
        "状況が違ったら、同じことをしていたと思いますか？",
        "理想的には、どうなっていればよかったですか？",
    ],
}


class FollowUpGenerator:
    """
    Generates contextually grounded follow-up questions.
    AI-first with deterministic fallback. §50
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)

    async def generate(
        self,
        user_response: str,
        topic: str,
        stage: int,
        previous_followups: list[str] | None = None,
        current_depth: int = 1,
    ) -> FollowUpSpec:
        """
        Generate a contextual follow-up question.
        §51 depth progression: 1=fact, 2=why, 3=example, 4=comparison, 5=hypothetical
        """
        previous_followups = previous_followups or []
        depth = min(max(current_depth, 1), 5)

        # AI path
        try:
            spec = await self._generate_with_ai(
                user_response, topic, stage, previous_followups, depth
            )
            if spec:
                return spec
        except Exception as e:
            logger.warning(f"[FollowUpGenerator] AI failed: {e}")

        # Deterministic fallback
        return self._build_fallback(user_response, topic, depth)

    async def _generate_with_ai(
        self,
        user_response: str,
        topic: str,
        stage: int,
        previous_followups: list[str],
        depth: int,
    ) -> FollowUpSpec | None:
        sys_prompt, user_content = RampPrompts.build_followup_generation_prompt(
            user_response=user_response,
            topic=topic,
            stage=stage,
            previous_followups=previous_followups,
            current_depth=depth,
        )
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=user_content)],
            task=AITask.RAMP_FOLLOWUP_GENERATION,
            system_instruction=sys_prompt,
            temperature=0.7,
            max_output_tokens=300,
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
        )
        resp = await self.ai_router.generate(req)
        data = json.loads(resp.text)

        if not data.get("question_jp"):
            return None

        try:
            fu_type = FollowUpType(data.get("follow_up_type", "fact"))
        except ValueError:
            fu_type = FollowUpType.FACT

        return FollowUpSpec(
            question_jp=data["question_jp"],
            question_vi=data.get("question_vi"),
            follow_up_type=fu_type,
            depth_level=data.get("depth_level", depth),
            relates_to=data.get("relates_to"),
        )

    def _build_fallback(
        self,
        user_response: str,
        topic: str,
        depth: int,
    ) -> FollowUpSpec:
        """Deterministic fallback: pattern-based question from response keywords."""
        depth_map = {1: "fact", 2: "why", 3: "example", 4: "comparison", 5: "hypothetical"}
        type_key = depth_map.get(depth, "why")

        # Extract a keyword from the response for context
        keyword = self._extract_keyword(user_response)

        patterns = _FOLLOWUP_PATTERNS.get(type_key, _FOLLOWUP_PATTERNS["why"])
        question = patterns[hash(user_response) % len(patterns)]

        try:
            fu_type = FollowUpType(type_key)
        except ValueError:
            fu_type = FollowUpType.WHY

        return FollowUpSpec(
            question_jp=question,
            follow_up_type=fu_type,
            depth_level=depth,
            relates_to=keyword,
        )

    def _extract_keyword(self, text: str) -> str | None:
        """Extract a salient keyword from the response for context anchoring."""
        # Remove common function words, take the longest remaining token
        stop_chars = {"は", "が", "を", "に", "で", "と", "の", "も", "や", "て", "し", "ん", "な"}
        clean = re.sub(r"[。、！？\s]", " ", text)
        tokens = [t for t in clean.split() if t and t not in stop_chars and len(t) >= 2]
        if tokens:
            return max(tokens, key=len)
        return None

    def get_next_depth(
        self,
        current_depth: int,
        previous_followups: list[str],
        stage: int,
    ) -> int:
        """
        §51 Determine next follow-up depth.
        Progress through: fact(1) → why(2) → example(3) → comparison(4) → hypothetical(5)
        """
        max_depth = min(5, 1 + stage // 2)  # higher stages allow deeper follow-ups
        return min(current_depth + 1, max_depth)
