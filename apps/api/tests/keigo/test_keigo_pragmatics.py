"""Unit tests for Keigo Sociolinguistic Pragmatics & Politeness Matrix."""

from app.domains.keigo.double_keigo import DoubleKeigoAnalyzer
from app.domains.keigo.pragmatics import PragmaticsEngine
from app.domains.keigo.social_context import Group, PersonRole, Register, Situation, SocialContext


def test_double_keigo_no_false_positives_on_natural_polite_speech():
    """Verifies that natural sentences with multiple お/ご are NOT flagged as double keigo."""
    analyzer = DoubleKeigoAnalyzer()

    # Sentence with multiple お and ご that previously triggered markers >= 4 false positive
    text = "おはようございます、お茶をご用意いたしました"
    result = analyzer.analyze(text)
    assert not result["is_double_keigo"]
    assert result["status"] == "none"
    assert result["severity"] == "none"

    text2 = "お忙しいところ、ご足労いただき誠にありがとうございます"
    result2 = analyzer.analyze(text2)
    assert not result2["is_double_keigo"]
    assert result2["status"] == "none"


def test_double_keigo_detects_genuine_violations():
    """Verifies accurate detection of morphological double-keigo patterns."""
    analyzer = DoubleKeigoAnalyzer()

    # 1. お〜になられる (お書きになられる)
    res1 = analyzer.analyze("先生がお書きになられました")
    assert res1["is_double_keigo"]
    assert res1["status"] == "generally_inappropriate"
    assert "お書きになられ" in res1["offending_phrase"]

    # 2. おっしゃられる (おっしゃる + られる)
    res2 = analyzer.analyze("社長がおっしゃられた通りです")
    assert res2["is_double_keigo"]
    assert res2["status"] == "generally_inappropriate"
    assert "おっしゃられ" in res2["offending_phrase"]

    # 3. 拝見される (謙譲 + 尊敬の方向混同)
    res3 = analyzer.analyze("資料を拝見されましたか")
    assert res3["is_double_keigo"]
    assert "拝見され" in res3["offending_phrase"]

    # 4. お見えになられる
    res4 = analyzer.analyze("お客様がお見えになられました")
    assert res4["is_double_keigo"]


def test_double_keigo_whitelists_accepted_established_forms():
    """Verifies that established customary double keigo is accepted without penalty."""
    analyzer = DoubleKeigoAnalyzer()

    assert not analyzer.analyze("どうぞお召し上がりください")["is_double_keigo"]
    assert not analyzer.analyze("こちらをご覧ください")["is_double_keigo"]
    assert not analyzer.analyze("明日お伺いいたします")["is_double_keigo"]
    assert not analyzer.analyze("ご案内いたしますので少々お待ちください")["is_double_keigo"]


def test_baito_keigo_detection_and_suggestion():
    """Verifies detection of commercial manual keigo (Baito Keigo)."""
    engine = PragmaticsEngine()
    ctx = SocialContext(
        listener_role=PersonRole.CUSTOMER,
        listener_group=Group.SOTO,
        register_target=Register.BUSINESS_KEIGO,
    )

    # 1. 〜の方 (お水の方)
    res1 = engine.evaluate("お水の方をお持ちいたしました", ctx)
    assert res1["baito_keigo"]["found"]
    assert "「〜の方（ほう）」" in res1["baito_keigo"]["issues"][0]["pattern"]
    assert res1["naturalness"] < 0.80

    # 2. 〜からお預かり
    res2 = engine.evaluate("一万円からお預かりいたします", ctx)
    assert res2["baito_keigo"]["found"]
    assert "「〜からお預かり」" in res2["baito_keigo"]["issues"][0]["pattern"]

    # 3. よろしかったでしょうか
    res3 = engine.evaluate("こちらでよろしかったでしょうか", ctx)
    assert res3["baito_keigo"]["found"]
    assert "よろしかったでしょうか" in res3["baito_keigo"]["issues"][0]["pattern"]

    # Directional exception should NOT be flagged
    res_dir = engine.evaluate("あちらの方へお進みください", ctx)
    assert not res_dir["baito_keigo"]["found"]


def test_wakimae_relative_honorifics_in_group_humbling():
    """Verifies Ide's Wakimae relative honorific rule: humbling in-group superiors to Soto clients."""
    engine = PragmaticsEngine()
    # Speaking to Soto client about Uchi boss
    ctx = SocialContext(
        speaker_role=PersonRole.EMPLOYEE,
        speaker_group=Group.UCHI,
        listener_role=PersonRole.CLIENT,
        listener_group=Group.SOTO,
        referent_role=PersonRole.MANAGER,
        referent_group=Group.UCHI,
        business_context=True,
    )

    # Violation 1: Honoring in-group boss with title 社長様 to outside client
    res_violation1 = engine.evaluate("社長様はただいま席を外しております", ctx)
    assert res_violation1["wakimae"]["is_violation"]
    assert res_violation1["context_fit"] < 0.50

    # Violation 2: Using Sonkeigo for in-group boss's action to outside client
    res_violation2 = engine.evaluate("弊社社長がおっしゃいました", ctx)
    assert res_violation2["wakimae"]["is_violation"]
    assert res_violation2["context_fit"] < 0.50

    # Correct relative honorific: in-group boss referred to without title and humbled
    res_correct = engine.evaluate("社長の田中はただいま席を外しております", ctx)
    assert not res_correct["wakimae"]["is_violation"]
    assert res_correct["context_fit"] >= 0.85


def test_cushion_words_detection_and_bonus():
    """Verifies cushion words detection and communicative softness bonus on requests."""
    engine = PragmaticsEngine()
    ctx_request = SocialContext(
        listener_role=PersonRole.CUSTOMER,
        listener_group=Group.SOTO,
        situation=Situation.REQUEST,
        hierarchy_level=4,
    )

    # Request with cushion word
    text_with_cushion = "恐れ入りますが、こちらの書類にご署名をお願いできますでしょうか"
    res_cushion = engine.evaluate(text_with_cushion, ctx_request)
    assert res_cushion["cushion_words"]["found"]
    assert "恐れ入りますが" in res_cushion["cushion_words"]["detected_phrases"]
    assert res_cushion["cushion_words"]["bonus_applied"]
    assert res_cushion["context_fit"] >= 0.95

    # Request without cushion word
    text_no_cushion = "こちらの書類にご署名をお願いできますでしょうか"
    res_no_cushion = engine.evaluate(text_no_cushion, ctx_request)
    assert not res_no_cushion["cushion_words"]["found"]
    assert any("クッション言葉" in note for note in res_no_cushion["pedagogical_notes"])


def test_brown_levinson_politeness_matrix_weight():
    """Verifies P-D-R politeness calculation across contrasting social settings."""
    engine = PragmaticsEngine()

    # Extreme politeness: Outside CEO client + Apology
    ctx_high = SocialContext(
        listener_role=PersonRole.CUSTOMER,
        listener_group=Group.SOTO,
        situation=Situation.APOLOGY,
        familiarity_level=1,
        hierarchy_level=5,
    )
    res_high = engine.evaluate("大変申し訳ございませんでした", ctx_high)
    matrix_high = res_high["politeness_matrix"]
    assert matrix_high["power_distance_P"] >= 4.5
    assert matrix_high["social_distance_D"] >= 4.0
    assert matrix_high["ranking_of_imposition_R"] >= 4.5
    assert matrix_high["total_weight_W"] >= 13.0
    assert matrix_high["required_formality"] == "very_formal"

    # Low politeness: Close friend + casual chat
    ctx_low = SocialContext(
        listener_role=PersonRole.FRIEND,
        listener_group=Group.UCHI,
        situation=Situation.CASUAL_CHAT,
        familiarity_level=5,
        hierarchy_level=1,
        relationship=SocialContext().relationship.FRIENDLY,
        register_target=Register.TAMEGUCHI,
        business_context=False,
    )
    res_low = engine.evaluate("元気だった？", ctx_low)
    matrix_low = res_low["politeness_matrix"]
    assert matrix_low["total_weight_W"] <= 5.0
    assert matrix_low["required_formality"] == "casual"
