"""UchiSotoResolver — deterministic honorific direction reasoning."""

from __future__ import annotations

from dataclasses import dataclass

from app.domains.keigo.social_context import Group, PersonRole, SocialContext


@dataclass
class HonorificDirection:
    should_use_sonkeigo: bool
    should_use_kenjougo: bool
    should_use_teineigo: bool
    reason: str
    subject_is_soto: bool
    actor_group: Group


class UchiSotoResolver:
    """Resolves who is Uchi/Soto and which honorific direction is appropriate."""

    # Role -> default group (when not explicitly set)
    ROLE_GROUP_MAP: dict[PersonRole, Group] = {
        PersonRole.SELF: Group.UCHI,
        PersonRole.EMPLOYEE: Group.UCHI,
        PersonRole.COWORKER: Group.UCHI,
        PersonRole.MANAGER: Group.UCHI,
        PersonRole.EXECUTIVE: Group.UCHI,
        PersonRole.RECEPTIONIST: Group.UCHI,
        PersonRole.CUSTOMER: Group.SOTO,
        PersonRole.CLIENT: Group.SOTO,
        PersonRole.PARTNER: Group.SOTO,
        PersonRole.SALES_CONTACT: Group.SOTO,
        PersonRole.STRANGER: Group.SOTO,
        PersonRole.FRIEND: Group.SOTO,
        PersonRole.FAMILY: Group.UCHI,
    }

    def resolve_group(self, role: PersonRole, explicit: Group | None = None) -> Group:
        if explicit and explicit != Group.UNKNOWN:
            return explicit
        return self.ROLE_GROUP_MAP.get(role, Group.UNKNOWN)

    def resolve_direction(self, ctx: SocialContext, action_subject_role: PersonRole | None = None) -> HonorificDirection:
        """Determine honorific direction based on who performs action.

        - If subject is SOTO (customer, client, partner's action) → sonkeigo (elevate)
        - If subject is UCHI and listener is SOTO and action affects listener → kenjougo (humble)
        - Teineigo is baseline for business (always when business_context and not tameguchi target)
        """
        subject_role = action_subject_role or ctx.referent_role
        # Determine actor group: if subject is referent, use referent_group; if self, speaker_group
        if subject_role == PersonRole.SELF:
            actor_group = ctx.speaker_group
        elif subject_role == ctx.referent_role:
            actor_group = ctx.referent_group
        else:
            actor_group = self.resolve_group(subject_role)

        is_soto = actor_group == Group.SOTO
        is_uchi = actor_group == Group.UCHI
        listener_is_soto = ctx.listener_group == Group.SOTO

        should_sonkeigo = is_soto  # elevate Soto person's action
        should_kenjougo = is_uchi and listener_is_soto  # humble own action toward Soto
        should_teineigo = ctx.business_context and ctx.register_target != ctx.register_target.TAMEGUCHI if hasattr(ctx.register_target, "TAMEGUCHI") else ctx.business_context
        # Actually check register_target != TAMEGUCHI
        from app.domains.keigo.social_context import Register

        should_teineigo = ctx.business_context and ctx.register_target != Register.TAMEGUCHI

        if should_sonkeigo and should_kenjougo:
            # Both cannot be true for same subject; prefer sonkeigo if subject is Soto
            if is_soto:
                should_kenjougo = False
            else:
                should_sonkeigo = False

        reason_parts = []
        if should_sonkeigo:
            reason_parts.append(f"Subject {subject_role.value} is SOTO → 尊敬語")
        if should_kenjougo:
            reason_parts.append(f"Subject {subject_role.value} is UCHI acting toward SOTO listener {ctx.listener_role.value} → 謙譲語")
        if should_teineigo:
            reason_parts.append("Business context → 丁寧体 required")
        if not reason_parts:
            reason_parts.append("No honorific direction; casual/polite as per register")

        return HonorificDirection(
            should_use_sonkeigo=should_sonkeigo,
            should_use_kenjougo=should_kenjougo,
            should_use_teineigo=should_teineigo,
            reason="; ".join(reason_parts),
            subject_is_soto=is_soto,
            actor_group=actor_group,
        )

    def is_correct_direction(self, ctx: SocialContext, claimed_type: str, action_subject_role: PersonRole | None = None) -> tuple[bool, str]:
        """Check if claimed keigo type matches expected direction."""
        direction = self.resolve_direction(ctx, action_subject_role)
        claimed = claimed_type.lower()
        if "sonkeigo" in claimed or "尊敬" in claimed:
            if direction.should_use_sonkeigo:
                return True, "Sonkeigo direction correct"
            return False, f"Should not use sonkeigo here: {direction.reason}"
        if "kenjougo" in claimed or "謙譲" in claimed:
            if direction.should_use_kenjougo:
                return True, "Kenjougo direction correct"
            return False, f"Should not use kenjougo here: {direction.reason}"
        if "teineigo" in claimed or "丁寧" in claimed:
            if direction.should_use_teineigo:
                return True, "Teineigo appropriate"
            return False, "Teineigo not required for this register"
        return True, "No direction check"
