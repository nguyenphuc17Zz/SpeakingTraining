"""Keigo domain — Mode 2: Keigo & Register Studio."""

from app.domains.keigo.social_context import SocialContext, PersonRole, Group, Relationship, Situation
from app.domains.keigo.uchi_soto import UchiSotoResolver
from app.domains.keigo.register_engine import RegisterEngine, Register

__all__ = ["SocialContext", "PersonRole", "Group", "Relationship", "Situation", "UchiSotoResolver", "RegisterEngine", "Register"]
