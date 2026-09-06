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
class SocialNode:
    id: str
    name: str
    parent_id: str | None = None
    level_rank: int = 0  # 0=Entry/Junior, 1=Senior/Leader, 2=Kacho, 3=Bucho, 4=Executive/Shacho
    role: PersonRole = PersonRole.EMPLOYEE


class SocialHierarchyTree:
    """Multi-tiered social and corporate hierarchy DAG / Tree.

    Computes Lowest Common Ancestor (LCA) to determine Uchi/Soto in-group boundaries
    and pragmatic honorific requirements (Sonkeigo vs. Kenjougo).
    """

    def __init__(self):
        self.nodes: dict[str, SocialNode] = {}
        self.children: dict[str, list[str]] = {}

    def add_node(
        self,
        node_id: str,
        name: str,
        parent_id: str | None = None,
        level_rank: int = 0,
        role: PersonRole = PersonRole.EMPLOYEE,
    ) -> SocialNode:
        node = SocialNode(id=node_id, name=name, parent_id=parent_id, level_rank=level_rank, role=role)
        self.nodes[node_id] = node
        if parent_id:
            if parent_id not in self.children:
                self.children[parent_id] = []
            self.children[parent_id].append(node_id)
        return node

    def get_ancestors_with_depth(self, node_id: str) -> list[str]:
        """Returns list of ancestors from node_id up to the root."""
        ancestors = []
        curr: str | None = node_id
        visited = set()
        while curr and curr in self.nodes and curr not in visited:
            ancestors.append(curr)
            visited.add(curr)
            curr = self.nodes[curr].parent_id
        return ancestors

    def get_depth(self, node_id: str) -> int:
        """Returns tree depth of node (root has depth 0)."""
        return len(self.get_ancestors_with_depth(node_id)) - 1

    def get_lca(self, u: str, v: str) -> str | None:
        """Finds Lowest Common Ancestor (LCA) of nodes u and v."""
        if u not in self.nodes or v not in self.nodes:
            return None
        if u == v:
            return u

        ancestors_u = set(self.get_ancestors_with_depth(u))
        for anc in self.get_ancestors_with_depth(v):
            if anc in ancestors_u:
                return anc
        return None

    def determine_relative_relation(
        self,
        speaker_id: str,
        listener_id: str,
        referent_id: str,
    ) -> dict[str, Any]:
        """Evaluates relative Uchi/Soto relation between Speaker, Listener, and Referent via LCA.

        Rule:
        - If depth(LCA(Speaker, Referent)) > depth(LCA(Speaker, Listener)):
          Referent belongs to a tighter in-group with Speaker than Listener does.
          Therefore, Referent is UCHI relative to Listener.
          => Humbling (Kenjougo) required; honorific suffixes (様, 社長) forbidden.
        - If depth(LCA(Listener, Referent)) > depth(LCA(Speaker, Listener)):
          Referent belongs to Listener's group (SOTO from Speaker).
          => Respectful (Sonkeigo) required if Referent is higher/equal rank.
        - If LCA(Speaker, Referent) == LCA(Speaker, Listener):
          All three are within the same organizational scope.
          => Standard internal hierarchy applies based on level_rank.
        """
        lca_spk_ref = self.get_lca(speaker_id, referent_id)
        lca_spk_lis = self.get_lca(speaker_id, listener_id)

        d_spk_ref = self.get_depth(lca_spk_ref) if lca_spk_ref else -1
        d_spk_lis = self.get_depth(lca_spk_lis) if lca_spk_lis else -1

        spk_node = self.nodes.get(speaker_id)
        ref_node = self.nodes.get(referent_id)

        if d_spk_ref > d_spk_lis:
            return {
                "is_referent_uchi_to_listener": True,
                "required_register": "kenjougo",
                "lca_speaker_referent": lca_spk_ref,
                "lca_speaker_listener": lca_spk_lis,
                "depth_speaker_referent": d_spk_ref,
                "depth_speaker_listener": d_spk_lis,
                "reason": f"Referent is Uchi (LCA depth {d_spk_ref} > {d_spk_lis}) relative to external listener.",
            }

        is_superior = False
        if spk_node and ref_node:
            is_superior = ref_node.level_rank > spk_node.level_rank

        req = "sonkeigo" if is_superior else "teineigo"
        return {
            "is_referent_uchi_to_listener": False,
            "required_register": req,
            "lca_speaker_referent": lca_spk_ref,
            "lca_speaker_listener": lca_spk_lis,
            "depth_speaker_referent": d_spk_ref,
            "depth_speaker_listener": d_spk_lis,
            "reason": f"Referent is Soto or internal peer/superior (rank {ref_node.level_rank if ref_node else 0} vs {spk_node.level_rank if spk_node else 0}).",
        }

    @classmethod
    def build_standard_corporate_tree(cls) -> "SocialHierarchyTree":
        tree = cls()
        # Depth 0: Global root
        tree.add_node("root", "Business Society", parent_id=None, level_rank=0)

        # Depth 1: Organizations
        tree.add_node("my_company", "自社 (My Company)", parent_id="root", level_rank=0)
        tree.add_node("client_company", "取引先A社 (Client Company)", parent_id="root", level_rank=0)

        # Depth 2: Departments
        tree.add_node("sales_dept", "営業部", parent_id="my_company", level_rank=0)
        tree.add_node("dev_dept", "開発部", parent_id="my_company", level_rank=0)
        tree.add_node("client_procurement", "調達部", parent_id="client_company", level_rank=0)

        # Depth 3: People in My Company
        tree.add_node("speaker", "私 (Junior Sales)", parent_id="sales_dept", level_rank=0, role=PersonRole.SELF)
        tree.add_node("bucho_yamada", "山田部長", parent_id="sales_dept", level_rank=3, role=PersonRole.MANAGER)
        tree.add_node("shacho_suzuki", "鈴木社長", parent_id="my_company", level_rank=4, role=PersonRole.EXECUTIVE)

        # Depth 3: People in Client Company
        tree.add_node("client_tanaka", "田中様 (Client)", parent_id="client_procurement", level_rank=2, role=PersonRole.CLIENT)

        return tree


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

    # Hierarchical Graph Extension (LCA)
    social_tree: SocialHierarchyTree | None = None
    speaker_node_id: str | None = None
    listener_node_id: str | None = None
    referent_node_id: str | None = None

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
            "speaker_node_id": self.speaker_node_id,
            "listener_node_id": self.listener_node_id,
            "referent_node_id": self.referent_node_id,
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
            speaker_node_id=d.get("speaker_node_id"),
            listener_node_id=d.get("listener_node_id"),
            referent_node_id=d.get("referent_node_id"),
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

