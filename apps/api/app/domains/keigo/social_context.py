"""SocialContext model — deterministic context ontology (app-level, not vocabulary)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Group(str, Enum):
    UCHI = "uchi"
    SOTO = "soto"
    UNKNOWN = "unknown"


class PersonRole(str, Enum):
    SELF = "self"
    CUSTOMER = "customer"
    CLIENT = "client"
    COWORKER = "coworker"
    MANAGER = "manager"
    EXECUTIVE = "executive"
    PARTNER = "partner"
    FRIEND = "friend"
    FAMILY = "family"
    STRANGER = "stranger"
    SALES_CONTACT = "sales_contact"
    RECEPTIONIST = "receptionist"
    EMPLOYEE = "employee"


class Relationship(str, Enum):
    HIERARCHICAL = "hierarchical"
    PEER = "peer"
    CUSTOMER_PROVIDER = "customer_provider"
    FRIENDLY = "friendly"
    FAMILY = "family"
    STRANGER = "stranger"
    BUSINESS = "business"


class Situation(str, Enum):
    BUSINESS_MEETING = "business_meeting"
    PHONE = "phone"
    EMAIL = "email"
    RECEPTION = "reception"
    CASUAL_CHAT = "casual_chat"
    PRESENTATION = "presentation"
    APOLOGY = "apology"
    REQUEST = "request"
    INTRODUCTION = "introduction"
    SALES = "sales"


class Register(str, Enum):
    TAMEGUCHI = "tameguchi"
    POLITE = "polite"  # 丁寧体
    BUSINESS_POLITE = "business_polite"
    BUSINESS_KEIGO = "business_keigo"  # 尊敬/謙譲含むビジネス敬語
    VERY_FORMAL = "very_formal"


@dataclass
class SocialContext:
    speaker_role: PersonRole = PersonRole.SELF
    listener_role: PersonRole = PersonRole.CUSTOMER
    referent_role: PersonRole = PersonRole.SELF

    speaker_group: Group = Group.UCHI
    listener_group: Group = Group.SOTO
    referent_group: Group = Group.UCHI

    relationship: Relationship = Relationship.BUSINESS
    situation: Situation = Situation.BUSINESS_MEETING
    register_target: Register = Register.BUSINESS_KEIGO
    business_context: bool = True
    familiarity_level: int = 2  # 1-5 (1=初対面, 5=親しい)
    hierarchy_level: int = 3  # 1-5 (1=目下, 5=目上)

    def to_dict(self) -> dict:
        return {
            "speaker_role": self.speaker_role.value,
            "listener_role": self.listener_role.value,
            "referent_role": self.referent_role.value,
            "speaker_group": self.speaker_group.value,
            "listener_group": self.listener_group.value,
            "referent_group": self.referent_group.value,
            "relationship": self.relationship.value,
            "situation": self.situation.value,
            "register_target": self.register_target.value,
            "business_context": self.business_context,
            "familiarity_level": self.familiarity_level,
            "hierarchy_level": self.hierarchy_level,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SocialContext":
        def _enum(ecls, val, default):
            try:
                return ecls(val)
            except Exception:
                return default

        return cls(
            speaker_role=_enum(PersonRole, d.get("speaker_role"), PersonRole.SELF),
            listener_role=_enum(PersonRole, d.get("listener_role"), PersonRole.CUSTOMER),
            referent_role=_enum(PersonRole, d.get("referent_role"), PersonRole.SELF),
            speaker_group=_enum(Group, d.get("speaker_group"), Group.UCHI),
            listener_group=_enum(Group, d.get("listener_group"), Group.SOTO),
            referent_group=_enum(Group, d.get("referent_group"), Group.UCHI),
            relationship=_enum(Relationship, d.get("relationship"), Relationship.BUSINESS),
            situation=_enum(Situation, d.get("situation"), Situation.BUSINESS_MEETING),
            register_target=_enum(Register, d.get("register_target"), Register.BUSINESS_KEIGO),
            business_context=bool(d.get("business_context", True)),
            familiarity_level=int(d.get("familiarity_level", 2)),
            hierarchy_level=int(d.get("hierarchy_level", 3)),
        )


# Speech act ontology (small app-level, not vocabulary)
class SpeechAct(str, Enum):
    REQUEST = "request"
    APOLOGIZE = "apologize"
    CONFIRM = "confirm"
    REPORT = "report"
    INVITE = "invite"
    DECLINE = "decline"
    OFFER = "offer"
    THANK = "thank"
    TRANSFER = "transfer"
    INTRODUCE = "introduce"
    ASK = "ask"
    RESPOND = "respond"
    SCHEDULE = "schedule"
