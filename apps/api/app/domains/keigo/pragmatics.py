"""PragmaticsEngine — naturalness & business appropriateness."""

from __future__ import annotations

from app.domains.keigo.social_context import Register, SocialContext


class PragmaticsEngine:
    def evaluate(self, text: str, ctx: SocialContext, register: Register | None = None) -> dict:
        # Distinguish grammatically correct vs contextually awkward vs over/under formal
        target = register or ctx.register_target
        # Heuristic: very formal in casual friendly context = over-formal
        over_formal = False
        under_formal = False
        if ctx.relationship.value == "friendly" and ctx.familiarity_level >= 4 and target in (Register.BUSINESS_KEIGO, Register.VERY_FORMAL):
            if "でございます" in text or "させていただきます" in text:
                over_formal = True
        if ctx.business_context and target == Register.TAMEGUCHI and ("だ" in text and "です" not in text):
            under_formal = True
        # Literal translation detection: if text contains katakana loanword where native better? simplified
        naturalness = 0.85
        if over_formal:
            naturalness = 0.55
        if under_formal:
            naturalness = 0.6
        if len(text) > 80 and target == Register.TAMEGUCHI:
            naturalness = min(naturalness, 0.7)  # too long for casual

        return {
            "over_formal": over_formal,
            "under_formal": under_formal,
            "naturalness": naturalness,
            "register_fit": 0.55 if over_formal or under_formal else 0.9,
            "context_fit": 0.6 if over_formal or under_formal else 0.9,
        }
