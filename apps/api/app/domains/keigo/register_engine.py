"""RegisterEngine — deterministic register determination (multidimensional, not formal+1)."""

from __future__ import annotations

from dataclasses import dataclass

from app.domains.keigo.social_context import Register, Relationship, Situation, SocialContext


@dataclass
class RegisterDecision:
    register: Register
    confidence: float
    reason: str
    formality_level: int  # 1-5


class RegisterEngine:
    """Determines appropriate register from social context."""

    def decide(self, ctx: SocialContext) -> RegisterDecision:
        # Use explicit target if set and not contradictory
        if ctx.register_target != Register.TAMEGUCHI:
            # Check if target matches context reasonably
            expected = self.infer_from_context(ctx)
            if expected.register == ctx.register_target:
                return RegisterDecision(register=ctx.register_target, confidence=0.95, reason=f"Explicit target matches inferred {expected.register.value}", formality_level=expected.formality_level)
            # If explicit target conflicts strongly, still respect explicit but lower confidence
            if ctx.familiarity_level >= 4 and ctx.register_target in (Register.BUSINESS_KEIGO, Register.VERY_FORMAL):
                return RegisterDecision(register=ctx.register_target, confidence=0.6, reason="Explicit very formal but familiarity high — possible over-formal", formality_level=5)
            # Otherwise respect explicit
            # Map target to formality
            fmt_map = {
                Register.TAMEGUCHI: 1,
                Register.POLITE: 3,
                Register.BUSINESS_POLITE: 3,
                Register.BUSINESS_KEIGO: 4,
                Register.VERY_FORMAL: 5,
            }
            return RegisterDecision(register=ctx.register_target, confidence=0.85, reason="Respect explicit register_target", formality_level=fmt_map.get(ctx.register_target, 3))
        # No explicit or tameguchi -> infer
        return self.infer_from_context(ctx)

    def infer_from_context(self, ctx: SocialContext) -> RegisterDecision:
        # Hierarchy + relationship + situation
        if ctx.relationship == Relationship.FRIENDLY and ctx.familiarity_level >= 4 and not ctx.business_context:
            return RegisterDecision(Register.TAMEGUCHI, 0.9, "Friendly, familiar, non-business → tamenoguchi", 1)
        if ctx.relationship == Relationship.FAMILY and ctx.familiarity_level >= 4:
            return RegisterDecision(Register.TAMEGUCHI, 0.9, "Family → tamenoguchi", 1)
        if ctx.business_context:
            if ctx.hierarchy_level >= 4 or ctx.situation in (Situation.PRESENTATION, Situation.APOLOGY):
                return RegisterDecision(Register.BUSINESS_KEIGO, 0.92, "Business + high hierarchy or apology/presentation → business keigo", 4)
            if ctx.hierarchy_level >= 3 or ctx.situation in (Situation.BUSINESS_MEETING, Situation.PHONE, Situation.RECEPTION):
                if ctx.relationship == Relationship.CUSTOMER_PROVIDER:
                    return RegisterDecision(Register.BUSINESS_KEIGO, 0.88, "Customer-facing business → business keigo", 4)
                return RegisterDecision(Register.BUSINESS_POLITE, 0.85, "Business meeting/phone → business polite", 3)
            return RegisterDecision(Register.BUSINESS_POLITE, 0.8, "Business context default → business polite", 3)
        if ctx.situation == Situation.CASUAL_CHAT and ctx.familiarity_level >= 3:
            return RegisterDecision(Register.POLITE, 0.7, "Casual but not business → polite", 2)
        return RegisterDecision(Register.POLITE, 0.75, "Default polite", 2)

    def is_register_fit(self, actual: Register, expected: Register) -> tuple[bool, str]:
        if actual == expected:
            return True, "Register matches"
        # Allow near-misses: business_polite vs business_keigo are close
        close_pairs = {(Register.BUSINESS_POLITE, Register.BUSINESS_KEIGO), (Register.POLITE, Register.BUSINESS_POLITE)}
        if (actual, expected) in close_pairs or (expected, actual) in close_pairs:
            return False, f"Register close but not exact: {actual.value} vs {expected.value} (slightly under/over formal)"
        return False, f"Register mismatch: {actual.value} vs {expected.value}"
