"""Keigo domain — Mode 2: Keigo & Register Studio."""

from app.domains.keigo.register_engine import Register, RegisterEngine
from app.domains.keigo.social_context import Group, PersonRole, Relationship, Situation, SocialContext
from app.domains.keigo.uchi_soto import UchiSotoResolver

__all__ = ["SocialContext", "PersonRole", "Group", "Relationship", "Situation", "UchiSotoResolver", "RegisterEngine", "Register"]
