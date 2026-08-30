"""Keigo Vocabulary Pool — Complete honorific & humble word pairs, business words, and regular rules.

Organized into 4 practical categories:
- sonkeigo_irregular: Tôn kính ngữ bất quy tắc (18 core triplets)
- kenjougo_irregular: Khiêm nhường ngữ bất quy tắc (18 core triplets)
- rule_based: Kính ngữ theo quy tắc (お〜になる ↔ お〜する/いたす, ご〜なさる/いたす)
- business_words: Đại từ, danh từ & phó từ thương mại (人→方, 会社→弊社/貴社, 今日→本日...)

Usage:
    from app.domains.keigo.keigo_vocab_pool import (
        ALL_KEIGO_WORDS, KeigoWordEntry, get_all_keigo_vocab,
        get_sonkeigo_pool, get_kenjougo_pool, get_rule_based_pool,
        get_business_vocab_pool, get_keigo_by_category, search_keigo
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class KeigoWordEntry:
    source_word: str  # Plain word (e.g., 食べる, 行く, 今日, 会社)
    source_reading: str  # e.g., たべる
    meaning_vi: str  # e.g., ăn, đi, hôm nay
    target_type: str  # 'sonkeigo' | 'kenjougo' | 'business' | 'rule_based'
    target_label_vi: str  # 'Tôn kính ngữ (尊敬語)' | 'Khiêm nhường ngữ (謙譲語)' | 'Từ thương mại (ビジネス語)'
    canonical: str  # Primary answer (e.g., 召し上がる, 参る, 本日)
    canonical_reading: str  # e.g., めしあがる
    acceptable_variants: list[str] = field(default_factory=list)
    triplet_sonkeigo: str | None = None
    triplet_kenjougo: str | None = None
    category: str = "sonkeigo_irregular"  # 'sonkeigo_irregular' | 'kenjougo_irregular' | 'rule_based' | 'business_words'
    jlpt_level: str = "N3"
    explanation_vi: str = ""
    subject_hint_vi: str = ""  # '👑 Hành động của: SẾP / ĐỐI TÁC / KHÁCH HÀNG' | '🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH'
    formula: str = ""  # 'Bất quy tắc (Đặc biệt)' | 'お + V(bỏ ます) + になる' | 'お + V(bỏ ます) + いたす'
    example_ja: str = ""
    example_vi: str = ""


# ==============================================================================
# 1. CORE SONKEIGO IRREGULAR (Tôn kính ngữ bất quy tắc — Đối phương thực hiện)
# ==============================================================================
SONKEIGO_IRREGULAR: list[KeigoWordEntry] = [
    KeigoWordEntry(
        source_word="する",
        source_reading="する",
        meaning_vi="làm",
        target_type="sonkeigo",
        target_label_vi="Tôn kính ngữ (尊敬語)",
        canonical="なさる",
        canonical_reading="なさる",
        acceptable_variants=["なさる", "なさいます", "なさって", "なされる"],
        triplet_sonkeigo="なさる",
        triplet_kenjougo="いたす",
        category="sonkeigo_irregular",
        jlpt_level="N4",
        explanation_vi="Hành động của đối phương/khách hàng → なさる",
        subject_hint_vi="👑 Hành động của: SẾP / ĐỐI TÁC / KHÁCH HÀNG",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「本日の午後はどのようなご予定をなさいますか？」",
        example_vi="Chiều nay quý khách đã có kế hoạch như thế nào rồi ạ?",
    ),
    KeigoWordEntry(
        source_word="行く",
        source_reading="いく",
        meaning_vi="đi",
        target_type="sonkeigo",
        target_label_vi="Tôn kính ngữ (尊敬語)",
        canonical="いらっしゃる",
        canonical_reading="いらっしゃる",
        acceptable_variants=["いらっしゃる", "いらっしゃいます", "おいでになる", "おいでになります"],
        triplet_sonkeigo="いらっしゃる / おいでになる",
        triplet_kenjougo="参る / 伺う",
        category="sonkeigo_irregular",
        jlpt_level="N4",
        explanation_vi="Đối phương đi đâu → いらっしゃる (hoặc おいでになる)",
        subject_hint_vi="👑 Hành động của: SẾP / ĐỐI TÁC / KHÁCH HÀNG",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「社長は明日、大阪の支社へいらっしゃいます。」",
        example_vi="Ngày mai Giám đốc sẽ đến chi nhánh Osaka ạ.",
    ),
    KeigoWordEntry(
        source_word="来る",
        source_reading="くる",
        meaning_vi="đến",
        target_type="sonkeigo",
        target_label_vi="Tôn kính ngữ (尊敬語)",
        canonical="いらっしゃる",
        canonical_reading="いらっしゃる",
        acceptable_variants=["いらっしゃる", "いらっしゃいます", "お越しになる", "お見えになる"],
        triplet_sonkeigo="いらっしゃる / お越しになる",
        triplet_kenjougo="参る",
        category="sonkeigo_irregular",
        jlpt_level="N4",
        explanation_vi="Khách đến công ty → いらっしゃる / お越しになる",
        subject_hint_vi="👑 Hành động của: SẾP / ĐỐI TÁC / KHÁCH HÀNG",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「本日は遠いところをお越しいただきありがとうございます。」",
        example_vi="Cảm ơn quý khách hôm nay đã không quản đường xa đến đây ạ.",
    ),
    KeigoWordEntry(
        source_word="居る",
        source_reading="いる",
        meaning_vi="ở / có mặt",
        target_type="sonkeigo",
        target_label_vi="Tôn kính ngữ (尊敬語)",
        canonical="いらっしゃる",
        canonical_reading="いらっしゃる",
        acceptable_variants=["いらっしゃる", "いらっしゃいます", "おいでになる"],
        triplet_sonkeigo="いらっしゃる",
        triplet_kenjougo="おる",
        category="sonkeigo_irregular",
        jlpt_level="N4",
        explanation_vi="Sếp có ở văn phòng không → いらっしゃいますか",
        subject_hint_vi="👑 Hành động của: SẾP / ĐỐI TÁC / KHÁCH HÀNG",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「田中部長はただいまお席にいらっしゃいますか？」",
        example_vi="Xin hỏi Trưởng phòng Tanaka hiện có đang ở bàn làm việc không ạ?",
    ),
    KeigoWordEntry(
        source_word="言う",
        source_reading="いう",
        meaning_vi="nói",
        target_type="sonkeigo",
        target_label_vi="Tôn kính ngữ (尊敬語)",
        canonical="おっしゃる",
        canonical_reading="おっしゃる",
        acceptable_variants=["おっしゃる", "おっしゃいます", "おっしゃって"],
        triplet_sonkeigo="おっしゃる",
        triplet_kenjougo="申す / 申し上げる",
        category="sonkeigo_irregular",
        jlpt_level="N4",
        explanation_vi="Khách hàng nói → おっしゃる",
        subject_hint_vi="👑 Hành động của: SẾP / ĐỐI TÁC / KHÁCH HÀNG",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「お客様がおっしゃった通りに手配いたしました。」",
        example_vi="Tôi đã thu xếp đúng như lời quý khách đã dặn bảo ạ.",
    ),
    KeigoWordEntry(
        source_word="食べる",
        source_reading="たべる",
        meaning_vi="ăn",
        target_type="sonkeigo",
        target_label_vi="Tôn kính ngữ (尊敬語)",
        canonical="召し上がる",
        canonical_reading="めしあがる",
        acceptable_variants=["召し上がる", "召し上がります", "めしあがる", "めしあがります"],
        triplet_sonkeigo="召し上がる",
        triplet_kenjougo="いただく",
        category="sonkeigo_irregular",
        jlpt_level="N4",
        explanation_vi="Mời khách ăn dùng bữa → 召し上がる",
        subject_hint_vi="👑 Hành động của: SẾP / ĐỐI TÁC / KHÁCH HÀNG",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「どうぞ温かいうちにお召し上がりください。」",
        example_vi="Món ăn còn đang nóng, xin kính mời quý khách dùng bữa ạ.",
    ),
    KeigoWordEntry(
        source_word="飲む",
        source_reading="のむ",
        meaning_vi="uống",
        target_type="sonkeigo",
        target_label_vi="Tôn kính ngữ (尊敬語)",
        canonical="召し上がる",
        canonical_reading="めしあがる",
        acceptable_variants=["召し上がる", "召し上がります", "めしあがる", "めしあがります"],
        triplet_sonkeigo="召し上がる",
        triplet_kenjougo="いただく",
        category="sonkeigo_irregular",
        jlpt_level="N4",
        explanation_vi="Mời sếp uống trà → 召し上がる",
        subject_hint_vi="👑 Hành động của: SẾP / ĐỐI TÁC / KHÁCH HÀNG",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「お飲み物は何を召し上がりますか？」",
        example_vi="Quý khách muốn dùng đồ uống gì ạ?",
    ),
    KeigoWordEntry(
        source_word="見る",
        source_reading="みる",
        meaning_vi="xem / nhìn",
        target_type="sonkeigo",
        target_label_vi="Tôn kính ngữ (尊敬語)",
        canonical="ご覧になる",
        canonical_reading="ごらんになる",
        acceptable_variants=["ご覧になる", "ご覧になります", "ごらんになる", "ごらんになります"],
        triplet_sonkeigo="ご覧になる",
        triplet_kenjougo="拝見する",
        category="sonkeigo_irregular",
        jlpt_level="N4",
        explanation_vi="Xin mời sếp xem tài liệu → ご覧になる",
        subject_hint_vi="👑 Hành động của: SẾP / ĐỐI TÁC / KHÁCH HÀNG",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「こちらの資料をぜひご覧になってください。」",
        example_vi="Kính mời quý vị xem qua tập tài liệu đính kèm này ạ.",
    ),
    KeigoWordEntry(
        source_word="知る",
        source_reading="しる",
        meaning_vi="biết",
        target_type="sonkeigo",
        target_label_vi="Tôn kính ngữ (尊敬語)",
        canonical="ご存知だ",
        canonical_reading="ごぞんじだ",
        acceptable_variants=["ご存知だ", "ご存知です", "ご存じだ", "ご存じです", "ご存知ですか", "ご存じですか"],
        triplet_sonkeigo="ご存知だ / ご存知です",
        triplet_kenjougo="存じる / 存じ上げる",
        category="sonkeigo_irregular",
        jlpt_level="N4",
        explanation_vi="Quý khách có biết chuyện đó không → ご存知ですか",
        subject_hint_vi="👑 Hành động của: SẾP / ĐỐI TÁC / KHÁCH HÀNG",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「こちらの新しいサービスをご存知でしょうか？」",
        example_vi="Quý khách đã biết đến dịch vụ mới này của bên em chưa ạ?",
    ),
    KeigoWordEntry(
        source_word="くれる",
        source_reading="くれる",
        meaning_vi="cho tôi / tặng tôi",
        target_type="sonkeigo",
        target_label_vi="Tôn kính ngữ (尊敬語)",
        canonical="くださる",
        canonical_reading="くださる",
        acceptable_variants=["くださる", "くださいます", "ください"],
        triplet_sonkeigo="くださる",
        triplet_kenjougo="差し上げる",
        category="sonkeigo_irregular",
        jlpt_level="N4",
        explanation_vi="Sếp cho tôi lời khuyên → くださる",
        subject_hint_vi="👑 Hành động của: SẾP / ĐỐI TÁC / KHÁCH HÀNG",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「部長が貴重なアドバイスをくださいました。」",
        example_vi="Trưởng phòng đã ban tặng cho tôi những lời khuyên vô cùng quý giá.",
    ),
    KeigoWordEntry(
        source_word="会う",
        source_reading="あう",
        meaning_vi="gặp",
        target_type="sonkeigo",
        target_label_vi="Tôn kính ngữ (尊敬語)",
        canonical="お目にかかる",
        canonical_reading="おめにかかる",
        acceptable_variants=["お会いになる", "お会いになります", "お目にかかる"],
        triplet_sonkeigo="お会いになる",
        triplet_kenjougo="お目にかかる",
        category="sonkeigo_irregular",
        jlpt_level="N3",
        explanation_vi="Sếp đi gặp khách hàng → お会いになる",
        subject_hint_vi="👑 Hành động của: SẾP / ĐỐI TÁC / KHÁCH HÀNG",
        formula="お + V(bỏ ます) + になる",
        example_ja="「社長は本日、取引先の代表とお会いになります。」",
        example_vi="Hôm nay Giám đốc sẽ diện kiến đại diện bên đối tác ạ.",
    ),
    KeigoWordEntry(
        source_word="寝る",
        source_reading="ねる",
        meaning_vi="ngủ",
        target_type="sonkeigo",
        target_label_vi="Tôn kính ngữ (尊敬語)",
        canonical="お休みになる",
        canonical_reading="おやすみになる",
        acceptable_variants=["お休みになる", "お休みになります"],
        triplet_sonkeigo="お休みになる",
        triplet_kenjougo="休ませていただく",
        category="sonkeigo_irregular",
        jlpt_level="N4",
        explanation_vi="Chúc sếp ngủ ngon → お休みになる",
        subject_hint_vi="👑 Hành động của: SẾP / ĐỐI TÁC / KHÁCH HÀNG",
        formula="お + V(bỏ ます) + になる",
        example_ja="「どうぞごゆっくりお休みになってください。」",
        example_vi="Kính chúc quý khách nghỉ ngơi thật thoải mái ạ.",
    ),
]

# ==============================================================================
# 2. CORE KENJOUGO IRREGULAR (Khiêm nhường ngữ bất quy tắc — Bản thân thực hiện)
# ==============================================================================
KENJOUGO_IRREGULAR: list[KeigoWordEntry] = [
    KeigoWordEntry(
        source_word="する",
        source_reading="する",
        meaning_vi="làm",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="いたす",
        canonical_reading="いたす",
        acceptable_variants=["いたす", "いたします", "致す", "致します"],
        triplet_sonkeigo="なさる",
        triplet_kenjougo="いたす",
        category="kenjougo_irregular",
        jlpt_level="N4",
        explanation_vi="Bản thân/công ty mình làm → いたす (いたします)",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「私どもが責任を持って対応いたします。」",
        example_vi="Bên chúng tôi xin phép chịu trách nhiệm giải quyết việc này ạ.",
    ),
    KeigoWordEntry(
        source_word="行く",
        source_reading="いく",
        meaning_vi="đi",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="参る",
        canonical_reading="まいる",
        acceptable_variants=["参る", "参ります", "まいる", "まいります", "伺う", "伺います"],
        triplet_sonkeigo="いらっしゃる / おいでになる",
        triplet_kenjougo="参る / 伺う",
        category="kenjougo_irregular",
        jlpt_level="N4",
        explanation_vi="Tôi xin phép đi đến → 参る (hoặc 伺う khi đi đến gặp ai)",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「明日の10時に御社へ伺います。」",
        example_vi="10 giờ sáng mai tôi xin phép được đến thăm quý công ty ạ.",
    ),
    KeigoWordEntry(
        source_word="来る",
        source_reading="くる",
        meaning_vi="đến",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="参る",
        canonical_reading="まいる",
        acceptable_variants=["参る", "参ります", "まいる", "まいります"],
        triplet_sonkeigo="いらっしゃる / お越しになる",
        triplet_kenjougo="参る",
        category="kenjougo_irregular",
        jlpt_level="N4",
        explanation_vi="Tôi từ chi nhánh đến → 参りました",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「ベトナム支社から参りましたグエンと申します。」",
        example_vi="Tôi là Nguyen, đến từ chi nhánh Việt Nam ạ.",
    ),
    KeigoWordEntry(
        source_word="居る",
        source_reading="いる",
        meaning_vi="ở / có mặt",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="おる",
        canonical_reading="おる",
        acceptable_variants=["おる", "おります"],
        triplet_sonkeigo="いらっしゃる",
        triplet_kenjougo="おる",
        category="kenjougo_irregular",
        jlpt_level="N4",
        explanation_vi="Tôi đang ở phòng họp → おります",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「私は午後5時までオフィスにおります。」",
        example_vi="Tôi sẽ ở lại văn phòng cho đến 5 giờ chiều ạ.",
    ),
    KeigoWordEntry(
        source_word="言う",
        source_reading="いう",
        meaning_vi="nói / tên là",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="申す",
        canonical_reading="もうす",
        acceptable_variants=["申す", "申します", "申し上げる", "申し上げます"],
        triplet_sonkeigo="おっしゃる",
        triplet_kenjougo="申す / 申し上げる",
        category="kenjougo_irregular",
        jlpt_level="N4",
        explanation_vi="Tôi tên là Tanaka → 田中と申します",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「営業部のナムと申します。よろしくお願いいたします。」",
        example_vi="Tôi là Nam đến từ phòng Kinh doanh. Rất mong được giúp đỡ ạ.",
    ),
    KeigoWordEntry(
        source_word="食べる",
        source_reading="たべる",
        meaning_vi="ăn",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="いただく",
        canonical_reading="いただく",
        acceptable_variants=["いただく", "いただきます", "頂く", "頂きます"],
        triplet_sonkeigo="召し上がる",
        triplet_kenjougo="いただく",
        category="kenjougo_irregular",
        jlpt_level="N4",
        explanation_vi="Tôi xin phép dùng bữa → いただきます",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「お土産のお菓子、大変美味しくいただきました。」",
        example_vi="Bánh kẹo quà tặng của quý vị, chúng tôi đã thưởng thức rất ngon miệng ạ.",
    ),
    KeigoWordEntry(
        source_word="飲む",
        source_reading="のむ",
        meaning_vi="uống",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="いただく",
        canonical_reading="いただく",
        acceptable_variants=["いただく", "いただきます", "頂く", "頂きます"],
        triplet_sonkeigo="召し上がる",
        triplet_kenjougo="いただく",
        category="kenjougo_irregular",
        jlpt_level="N4",
        explanation_vi="Tôi xin phép uống trà → いただきます",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「お茶を遠慮なくいただきます。」",
        example_vi="Tôi xin phép không khách sáo dùng trà ạ.",
    ),
    KeigoWordEntry(
        source_word="見る",
        source_reading="みる",
        meaning_vi="xem / nhìn",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="拝見する",
        canonical_reading="はいけんする",
        acceptable_variants=["拝見する", "拝見します", "はいけんする", "はいけんします", "拝見いたす", "拝見いたします"],
        triplet_sonkeigo="ご覧になる",
        triplet_kenjougo="拝見する",
        category="kenjougo_irregular",
        jlpt_level="N4",
        explanation_vi="Tôi đã xem qua email của quý đối tác → 拝見いたしました",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「お送りいただいたご提案書を拝見いたしました。」",
        example_vi="Tôi đã xem qua bản đề xuất mà quý công ty vừa gửi ạ.",
    ),
    KeigoWordEntry(
        source_word="知る",
        source_reading="しる",
        meaning_vi="biết",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="存じる",
        canonical_reading="ぞんじる",
        acceptable_variants=["存じる", "存じます", "存じております", "存じ上げます"],
        triplet_sonkeigo="ご存知だ",
        triplet_kenjougo="存じる / 存じ上げる",
        category="kenjougo_irregular",
        jlpt_level="N4",
        explanation_vi="Tôi có biết việc đó → 存じております",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「その件につきましては重々存じております。」",
        example_vi="Về vụ việc đó tôi đã nắm bắt và hiểu rất rõ rồi ạ.",
    ),
    KeigoWordEntry(
        source_word="もらう",
        source_reading="もらう",
        meaning_vi="nhận",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="いただく",
        canonical_reading="いただく",
        acceptable_variants=["いただく", "いただきます", "頂戴する", "ちょうだいする"],
        triplet_sonkeigo="お受け取りになる",
        triplet_kenjougo="いただく / 頂戴する",
        category="kenjougo_irregular",
        jlpt_level="N4",
        explanation_vi="Tôi nhận danh thiếp từ khách → 頂戴いたします",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「名刺を1枚頂戴いたします。」",
        example_vi="Tôi xin phép được nhận 1 tấm danh thiếp của quý vị ạ.",
    ),
    KeigoWordEntry(
        source_word="あげる",
        source_reading="あげる",
        meaning_vi="tặng / đưa cho",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="差し上げる",
        canonical_reading="さしあげる",
        acceptable_variants=["差し上げる", "差し上げます"],
        triplet_sonkeigo="くださる",
        triplet_kenjougo="差し上げる",
        category="kenjougo_irregular",
        jlpt_level="N4",
        explanation_vi="Tôi xin phép gửi tặng tài liệu → 差し上げます",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「後ほど詳しい資料を差し上げます。」",
        example_vi="Lát nữa tôi xin phép gửi tặng quý vị tài liệu chi tiết ạ.",
    ),
    KeigoWordEntry(
        source_word="会う",
        source_reading="あう",
        meaning_vi="gặp",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="お目にかかる",
        canonical_reading="おめにかかる",
        acceptable_variants=["お目にかかる", "お目にかかります"],
        triplet_sonkeigo="お会いになる",
        triplet_kenjougo="お目にかかる",
        category="kenjougo_irregular",
        jlpt_level="N3",
        explanation_vi="Rất vinh hạnh được gặp quý ngài → お目にかかれて光栄です",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「本日お目にかかれて大変光栄に存じます。」",
        example_vi="Hôm nay được diện kiến quý ngài tôi cảm thấy vô cùng vinh hạnh ạ.",
    ),
    KeigoWordEntry(
        source_word="聞く",
        source_reading="きく",
        meaning_vi="nghe / hỏi",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="伺う",
        canonical_reading="うかがう",
        acceptable_variants=["伺う", "伺います", "拝聴する", "はいちょうする"],
        triplet_sonkeigo="お聞きになる",
        triplet_kenjougo="伺う / 拝聴する",
        category="kenjougo_irregular",
        jlpt_level="N4",
        explanation_vi="Tôi xin phép hỏi ý kiến của sếp → 伺う",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="Bất quy tắc (Đặc biệt)",
        example_ja="「詳しいお話を伺ってもよろしいでしょうか？」",
        example_vi="Tôi xin phép được lắng nghe câu chuyện chi tiết được không ạ?",
    ),
]

# ==============================================================================
# 3. RULE-BASED KEIGO (Kính ngữ theo quy tắc: お〜になる / お〜いたす)
# ==============================================================================
RULE_BASED_KEIGO: list[KeigoWordEntry] = [
    KeigoWordEntry(
        source_word="連絡する",
        source_reading="れんらくする",
        meaning_vi="liên lạc",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="ご連絡いたす",
        canonical_reading="ごれんらくいたす",
        acceptable_variants=["ご連絡いたす", "ご連絡いたします", "ご連絡する", "ご連絡します"],
        triplet_sonkeigo="ご連絡なさる",
        triplet_kenjougo="ご連絡いたす",
        category="rule_based",
        jlpt_level="N3",
        explanation_vi="Bên tôi sẽ chủ động liên lạc lại → ご連絡いたします",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="ご + N(Hán tự) + いたす",
        example_ja="「確認が取れ次第、すぐにご連絡いたします。」",
        example_vi="Ngay sau khi xác nhận xong, tôi sẽ lập tức liên lạc lại ạ.",
    ),
    KeigoWordEntry(
        source_word="案内する",
        source_reading="あんないする",
        meaning_vi="hướng dẫn / dẫn đường",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="ご案内いたす",
        canonical_reading="ごあんないいたす",
        acceptable_variants=["ご案内いたす", "ご案内いたします", "ご案内する", "ご案内します"],
        triplet_sonkeigo="ご案内なさる",
        triplet_kenjougo="ご案内いたす",
        category="rule_based",
        jlpt_level="N3",
        explanation_vi="Tôi xin phép hướng dẫn đường đi → ご案内いたします",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="ご + N(Hán tự) + いたす",
        example_ja="「会議室まで私がご案内いたします。」",
        example_vi="Tôi xin phép được dẫn đường cho quý vị đến phòng họp ạ.",
    ),
    KeigoWordEntry(
        source_word="待つ",
        source_reading="まつ",
        meaning_vi="chờ đợi",
        target_type="sonkeigo",
        target_label_vi="Tôn kính ngữ (尊敬語)",
        canonical="お待ちになる",
        canonical_reading="おまちになる",
        acceptable_variants=["お待ちになる", "お待ちになります", "お待ちください"],
        triplet_sonkeigo="お待ちになる",
        triplet_kenjougo="お待ちする",
        category="rule_based",
        jlpt_level="N4",
        explanation_vi="Xin mời quý khách đợi một chút → 少々お待ちください",
        subject_hint_vi="👑 Hành động của: SẾP / ĐỐI TÁC / KHÁCH HÀNG",
        formula="お + V(bỏ ます) + になる",
        example_ja="「担当者が参りますので、少々お待ちになってください。」",
        example_vi="Người phụ trách sắp tới, xin kính mời quý khách đợi một lát ạ.",
    ),
    KeigoWordEntry(
        source_word="持つ",
        source_reading="もつ",
        meaning_vi="cầm / mang giúp",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="お持ちする",
        canonical_reading="おもちする",
        acceptable_variants=["お持ちする", "お持ちします", "お持ちいたす", "お持ちいたします"],
        triplet_sonkeigo="お持ちになる",
        triplet_kenjougo="お持ちする",
        category="rule_based",
        jlpt_level="N4",
        explanation_vi="Để tôi xách hành lý giúp quý khách → お持ちいたします",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="お + V(bỏ ます) + いたす",
        example_ja="「重いお荷物は私がロビーまでお持ちいたします。」",
        example_vi="Hành lý nặng để tôi xin phép xách ra sảnh giúp quý khách ạ.",
    ),
    KeigoWordEntry(
        source_word="届ける",
        source_reading="とどける",
        meaning_vi="giao đến",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="お届けする",
        canonical_reading="おとどけする",
        acceptable_variants=["お届けする", "お届けします", "お届けいたす", "お届けいたします"],
        triplet_sonkeigo="お届けになる",
        triplet_kenjougo="お届けする",
        category="rule_based",
        jlpt_level="N3",
        explanation_vi="Bên tôi sẽ giao tài liệu đến trong hôm nay → お届けいたします",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="お + V(bỏ ます) + いたす",
        example_ja="「本日中に請求書をお届けいたします。」",
        example_vi="Tôi xin phép được giao hóa đơn đến trong ngày hôm nay ạ.",
    ),
    KeigoWordEntry(
        source_word="手伝う",
        source_reading="てつだう",
        meaning_vi="giúp đỡ",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="お手伝いする",
        canonical_reading="おてつだいする",
        acceptable_variants=["お手伝いする", "お手伝いします", "お手伝いいたす", "お手伝いいたします"],
        triplet_sonkeigo="お手伝いになる",
        triplet_kenjougo="お手伝いする",
        category="rule_based",
        jlpt_level="N4",
        explanation_vi="Để tôi phụ giúp chuẩn bị → お手伝いいたします",
        subject_hint_vi="🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH",
        formula="お + V(bỏ ます) + いたす",
        example_ja="「会場の準備を喜んでお手伝いいたします。」",
        example_vi="Tôi rất sẵn lòng phụ giúp chuẩn bị hội trường ạ.",
    ),
]

# ==============================================================================
# 4. BUSINESS NOUNS & PRONOUNS (Từ xưng hô & Đại từ thương mại)
# ==============================================================================
BUSINESS_WORDS: list[KeigoWordEntry] = [
    KeigoWordEntry(
        source_word="人",
        source_reading="ひと",
        meaning_vi="người",
        target_type="business",
        target_label_vi="Từ xưng hô lịch sự (ビジネス語)",
        canonical="方",
        canonical_reading="かた",
        acceptable_variants=["方", "かた", "皆様", "みなさま"],
        category="business_words",
        jlpt_level="N5",
        explanation_vi="Người kia → あの方 (あのかた)",
        subject_hint_vi="💼 Từ xưng hô & Giao tiếp công sở",
        formula="Biến đổi từ vựng thương mại",
        example_ja="「あちらにいらっしゃる方はどなたでしょうか？」",
        example_vi="Xin hỏi vị đứng ở đằng kia là ai thế ạ?",
    ),
    KeigoWordEntry(
        source_word="だれ",
        source_reading="だれ",
        meaning_vi="ai",
        target_type="business",
        target_label_vi="Từ xưng hô lịch sự (ビジネス語)",
        canonical="どなた",
        canonical_reading="どなた",
        acceptable_variants=["どなた", "どちら様", "どちらさま"],
        category="business_words",
        jlpt_level="N5",
        explanation_vi="Xin hỏi ngài là ai → どちら様でしょうか / どなた様",
        subject_hint_vi="💼 Từ xưng hô & Giao tiếp công sở",
        formula="Biến đổi từ vựng thương mại",
        example_ja="「失礼ですが、どちら様でしょうか？」",
        example_vi="Xin thứ lỗi, xin hỏi quý khách là ai ạ?",
    ),
    KeigoWordEntry(
        source_word="どこ",
        source_reading="どこ",
        meaning_vi="ở đâu / phía nào",
        target_type="business",
        target_label_vi="Từ xưng hô lịch sự (ビジネス語)",
        canonical="どちら",
        canonical_reading="どちら",
        acceptable_variants=["どちら", "どちら様"],
        category="business_words",
        jlpt_level="N5",
        explanation_vi="Phòng họp ở đâu → 会議室はどちらでしょうか",
        subject_hint_vi="💼 Từ xưng hô & Giao tiếp công sở",
        formula="Biến đổi từ vựng thương mại",
        example_ja="「お手洗いはどちらにございますでしょうか？」",
        example_vi="Xin hỏi nhà vệ sinh nằm ở phía nào vậy ạ?",
    ),
    KeigoWordEntry(
        source_word="どう",
        source_reading="どう",
        meaning_vi="thế nào",
        target_type="business",
        target_label_vi="Từ xưng hô lịch sự (ビジネス語)",
        canonical="いかが",
        canonical_reading="いかが",
        acceptable_variants=["いかが", "いかがでしょうか"],
        category="business_words",
        jlpt_level="N5",
        explanation_vi="Ý kiến ngài thế nào → いかがでしょうか",
        subject_hint_vi="💼 Từ xưng hô & Giao tiếp công sở",
        formula="Biến đổi từ vựng thương mại",
        example_ja="「こちらのご提案はいかがでしょうか？」",
        example_vi="Bản đề xuất này của bên em quý ngài thấy thế nào ạ?",
    ),
    KeigoWordEntry(
        source_word="会社 (bên mình)",
        source_reading="かいしゃ",
        meaning_vi="công ty của mình",
        target_type="business",
        target_label_vi="Từ xưng hô lịch sự (ビジネス語)",
        canonical="弊社",
        canonical_reading="へいしゃ",
        acceptable_variants=["弊社", "へいしゃ", "わたくしども"],
        category="business_words",
        jlpt_level="N3",
        explanation_vi="Công ty của mình khi nói với khách → 弊社 (hoặc わが社)",
        subject_hint_vi="💼 Từ xưng hô & Giao tiếp công sở",
        formula="Biến đổi từ vựng thương mại",
        example_ja="「弊社の担当より折り返しお電話を差し上げます。」",
        example_vi="Người phụ trách bên công ty tôi sẽ gọi điện lại cho quý vị ạ.",
    ),
    KeigoWordEntry(
        source_word="会社 (bên khách)",
        source_reading="かいしゃ",
        meaning_vi="công ty của khách",
        target_type="business",
        target_label_vi="Từ xưng hô lịch sự (ビジネス語)",
        canonical="貴社",
        canonical_reading="きしゃ",
        acceptable_variants=["貴社", "きしゃ", "御社", "おんしゃ"],
        category="business_words",
        jlpt_level="N3",
        explanation_vi="Công ty của khách (khi nói) → 御社 (おんしゃ), khi viết → 貴社 (きしゃ)",
        subject_hint_vi="💼 Từ xưng hô & Giao tiếp công sở",
        formula="Biến đổi từ vựng thương mại",
        example_ja="「御社のますますのご発展を心よりお祈り申し上げます。」",
        example_vi="Chúng tôi chân thành kính chúc quý công ty ngày càng phát triển thịnh vượng.",
    ),
    KeigoWordEntry(
        source_word="今日",
        source_reading="きょう",
        meaning_vi="hôm nay",
        target_type="business",
        target_label_vi="Từ thương mại lịch sự (ビジネス語)",
        canonical="本日",
        canonical_reading="ほんじつ",
        acceptable_variants=["本日", "ほんじつ"],
        category="business_words",
        jlpt_level="N4",
        explanation_vi="Hôm nay trong thư từ & công sở → 本日 (ほんじつ)",
        subject_hint_vi="💼 Từ xưng hô & Giao tiếp công sở",
        formula="Biến đổi từ vựng thương mại",
        example_ja="「本日はご多忙の中、お時間をいただき恐れ入ります。」",
        example_vi="Hôm nay trong lúc bận rộn quý vị đã dành thời gian cho chúng tôi, thật cảm kích ạ.",
    ),
    KeigoWordEntry(
        source_word="明日",
        source_reading="あした",
        meaning_vi="ngày mai",
        target_type="business",
        target_label_vi="Từ thương mại lịch sự (ビジネス語)",
        canonical="明日",
        canonical_reading="みょうにち",
        acceptable_variants=["明日", "みょうにち", "あす"],
        category="business_words",
        jlpt_level="N3",
        explanation_vi="Ngày mai lịch sự → 明日 (みょうにち / あす)",
        subject_hint_vi="💼 Từ xưng hô & Giao tiếp công sở",
        formula="Biến đổi từ vựng thương mại",
        example_ja="「明日、改めてご連絡申し上げます。」",
        example_vi="Ngày mai tôi xin phép được liên lạc lại với quý vị ạ.",
    ),
    KeigoWordEntry(
        source_word="昨日",
        source_reading="きのう",
        meaning_vi="hôm qua",
        target_type="business",
        target_label_vi="Từ thương mại lịch sự (ビジネス語)",
        canonical="昨日",
        canonical_reading="さくじつ",
        acceptable_variants=["昨日", "さくじつ"],
        category="business_words",
        jlpt_level="N3",
        explanation_vi="Hôm qua lịch sự trong công sở → 昨日 (さくじつ)",
        subject_hint_vi="💼 Từ xưng hô & Giao tiếp công sở",
        formula="Biến đổi từ vựng thương mại",
        example_ja="「昨日は大変お世話になりありがとうございました。」",
        example_vi="Hôm qua đã được quý vị quan tâm giúp đỡ rất nhiều, xin chân thành cảm ơn ạ.",
    ),
    KeigoWordEntry(
        source_word="いい",
        source_reading="いい",
        meaning_vi="được / tốt",
        target_type="business",
        target_label_vi="Từ thương mại lịch sự (ビジネス語)",
        canonical="よろしい",
        canonical_reading="よろしい",
        acceptable_variants=["よろしい", "よろしいでしょうか", "結構です", "けっこうです"],
        category="business_words",
        jlpt_level="N5",
        explanation_vi="Có được không → よろしいでしょうか",
        subject_hint_vi="💼 Từ xưng hô & Giao tiếp công sở",
        formula="Biến đổi từ vựng thương mại",
        example_ja="「こちらの内容でよろしいでしょうか？」",
        example_vi="Nội dung như thế này đã được chưa ạ?",
    ),
    KeigoWordEntry(
        source_word="ちょっと",
        source_reading="ちょっと",
        meaning_vi="một chút / một lát",
        target_type="business",
        target_label_vi="Từ thương mại lịch sự (ビジネス語)",
        canonical="少々",
        canonical_reading="しょうしょう",
        acceptable_variants=["少々", "しょうしょう", "少し"],
        category="business_words",
        jlpt_level="N4",
        explanation_vi="Xin đợi một chút → 少々お待ちください",
        subject_hint_vi="💼 Từ xưng hô & Giao tiếp công sở",
        formula="Biến đổi từ vựng thương mại",
        example_ja="「確認いたしますので、少々お待ちいただけますでしょうか？」",
        example_vi="Tôi xin phép kiểm tra lại, quý khách vui lòng đợi một chút được không ạ?",
    ),
]

# Combined Pool
ALL_KEIGO_WORDS: list[KeigoWordEntry] = (
    SONKEIGO_IRREGULAR + KENJOUGO_IRREGULAR + RULE_BASED_KEIGO + BUSINESS_WORDS
)

KEIGO_CATEGORY_MAP: dict[str, list[KeigoWordEntry]] = {
    "sonkeigo_irregular": SONKEIGO_IRREGULAR,
    "kenjougo_irregular": KENJOUGO_IRREGULAR,
    "rule_based": RULE_BASED_KEIGO,
    "business_words": BUSINESS_WORDS,
}


def get_all_keigo_vocab() -> list[KeigoWordEntry]:
    return ALL_KEIGO_WORDS


def get_sonkeigo_pool() -> list[KeigoWordEntry]:
    return SONKEIGO_IRREGULAR


def get_kenjougo_pool() -> list[KeigoWordEntry]:
    return KENJOUGO_IRREGULAR


def get_rule_based_pool() -> list[KeigoWordEntry]:
    return RULE_BASED_KEIGO


def get_business_vocab_pool() -> list[KeigoWordEntry]:
    return BUSINESS_WORDS


def get_easy_keigo_vocab() -> list[KeigoWordEntry]:
    return ALL_KEIGO_WORDS


def get_normal_keigo_vocab() -> list[KeigoWordEntry]:
    return ALL_KEIGO_WORDS


def get_hard_keigo_vocab() -> list[KeigoWordEntry]:
    return ALL_KEIGO_WORDS


def get_keigo_by_category(category: str) -> list[KeigoWordEntry]:
    if not category or category == "all":
        return ALL_KEIGO_WORDS
    if category in KEIGO_CATEGORY_MAP:
        return KEIGO_CATEGORY_MAP[category]
    if category == "sonkeigo":
        return SONKEIGO_IRREGULAR
    if category == "kenjougo":
        return KENJOUGO_IRREGULAR
    if category == "business":
        return BUSINESS_WORDS
    return ALL_KEIGO_WORDS


def search_keigo(query: str) -> list[KeigoWordEntry]:
    if not query.strip():
        return ALL_KEIGO_WORDS
    q = query.lower().strip()
    primary = [
        k for k in ALL_KEIGO_WORDS
        if q in k.source_word.lower()
        or q in k.source_reading.lower()
        or q in k.canonical.lower()
        or q in k.canonical_reading.lower()
        or q in k.meaning_vi.lower()
        or any(q in syn.lower() for syn in k.acceptable_variants)
        or q in (k.triplet_sonkeigo or "").lower()
        or q in (k.triplet_kenjougo or "").lower()
    ]
    if primary:
        return primary
    return [
        k for k in ALL_KEIGO_WORDS
        if q in k.example_ja.lower()
        or q in k.example_vi.lower()
        or q in k.explanation_vi.lower()
    ]
