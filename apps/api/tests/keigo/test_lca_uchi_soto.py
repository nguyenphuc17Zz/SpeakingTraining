import pytest

from app.domains.keigo.pragmatics import PragmaticsEngine
from app.domains.keigo.social_context import (
    Group,
    PersonRole,
    Register,
    Situation,
    SocialContext,
    SocialHierarchyTree,
)


def test_social_hierarchy_tree_lca_calculation():
    """Verify lowest common ancestor correctly reflects organizational containment."""
    tree = SocialHierarchyTree.build_standard_corporate_tree()

    # Speaker and bucho are both in sales_dept
    assert tree.get_lca("speaker", "bucho_yamada") == "sales_dept"

    # Speaker and company president have LCA at my_company
    assert tree.get_lca("speaker", "shacho_suzuki") == "my_company"

    # Speaker and external client have LCA at root (society)
    assert tree.get_lca("speaker", "client_tanaka") == "root"

    # Depth verification
    assert tree.get_depth("root") == 0
    assert tree.get_depth("my_company") == 1
    assert tree.get_depth("sales_dept") == 2
    assert tree.get_depth("speaker") == 3


def test_relative_uchi_soto_determination():
    """Verify LCA depth comparison mathematically establishes in-group vs out-group status."""
    tree = SocialHierarchyTree.build_standard_corporate_tree()

    # Case 1: Speaker talking to Client about Company President
    # LCA(Speaker, President) is my_company (depth 1)
    # LCA(Speaker, Client) is root (depth 0)
    # Because depth 1 > 0, President is Uchi relative to Client!
    rel_client = tree.determine_relative_relation(
        speaker_id="speaker",
        listener_id="client_tanaka",
        referent_id="shacho_suzuki",
    )
    assert rel_client["is_referent_uchi_to_listener"] is True
    assert rel_client["required_register"] == "kenjougo"
    assert rel_client["lca_speaker_referent"] == "my_company"
    assert rel_client["lca_speaker_listener"] == "root"

    # Case 2: Speaker talking to Colleague in Sales about Client
    # Client is outside company (Soto) -> Sonkeigo required
    rel_internal = tree.determine_relative_relation(
        speaker_id="speaker",
        listener_id="bucho_yamada",
        referent_id="client_tanaka",
    )
    assert rel_internal["is_referent_uchi_to_listener"] is False
    assert rel_internal["required_register"] == "sonkeigo"


def test_pragmatics_engine_lca_integration():
    """Verify PragmaticsEngine uses LCA tree to detect relative honorific violations."""
    tree = SocialHierarchyTree.build_standard_corporate_tree()
    engine = PragmaticsEngine()

    ctx = SocialContext(
        speaker_role=PersonRole.SELF,
        listener_role=PersonRole.CLIENT,
        referent_role=PersonRole.EXECUTIVE,
        speaker_group=Group.UCHI,
        listener_group=Group.SOTO,
        referent_group=Group.UCHI,
        social_tree=tree,
        speaker_node_id="speaker",
        listener_node_id="client_tanaka",
        referent_node_id="shacho_suzuki",
    )

    # 1. Violation: Addressing client while referring to own CEO with Sonkeigo (おっしゃいました)
    bad_text = "その件につきましては、弊社社長がおっしゃいました。"
    res_bad = engine.evaluate(bad_text, ctx)
    assert res_bad["wakimae"]["is_violation"] is True
    assert res_bad["wakimae"]["lca_analysis"] is not None
    assert res_bad["wakimae"]["lca_analysis"]["is_referent_uchi_to_listener"] is True
    assert res_bad["context_fit"] < 0.60

    # 2. Correct humble form: 社長の鈴木が申しました
    good_text = "その件につきましては、社長の鈴木が申しておりました。"
    res_good = engine.evaluate(good_text, ctx)
    assert res_good["wakimae"]["is_violation"] is False
    assert res_good["context_fit"] >= 0.85
