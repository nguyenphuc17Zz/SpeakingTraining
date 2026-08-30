"""Vocabulary Dictionary Pool for Reflex Vocabulary Mode (reflex_vocabulary).

Covers nouns (N5-N1), adjectives (N5-N1), and adverbs for all-word-type recall training.
Verbs are imported and wrapped from dictionary_pool.py to avoid duplication.

Usage:
    from app.domains.reflex.vocab_pool import (
        ALL_VOCAB_WORDS, EASY_VOCAB, NORMAL_VOCAB, HARD_VOCAB, DictWord
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DictWord:
    word: str             # 学校 / 食べる / きれい
    reading: str          # がっこう / たべる / きれい
    word_type: str        # noun | adj_i | adj_na | adverb | verb
    jlpt: str             # n5 | n4 | n3 | n2 | n1
    meaning_vi: str       # trường học
    synonyms_vi: list[str] = field(default_factory=list)  # accepted answer variants


# =========================================================================
# NOUNS — N5
# =========================================================================
N5_NOUNS: list[DictWord] = [
    DictWord("先生", "せんせい", "noun", "n5", "giáo viên", ["thầy giáo", "cô giáo", "thầy cô"]),
    DictWord("学生", "がくせい", "noun", "n5", "học sinh", ["sinh viên", "học viên"]),
    DictWord("友達", "ともだち", "noun", "n5", "bạn bè", ["bạn thân", "bạn"]),
    DictWord("家族", "かぞく", "noun", "n5", "gia đình", []),
    DictWord("家", "いえ", "noun", "n5", "nhà", ["ngôi nhà", "căn nhà"]),
    DictWord("会社", "かいしゃ", "noun", "n5", "công ty", ["doanh nghiệp"]),
    DictWord("電車", "でんしゃ", "noun", "n5", "tàu điện", ["xe điện", "tàu"]),
    DictWord("バス", "ばす", "noun", "n5", "xe buýt", ["xe bus"]),
    DictWord("本", "ほん", "noun", "n5", "cuốn sách", ["sách"]),
    DictWord("映画", "えいが", "noun", "n5", "phim", ["điện ảnh", "phim ảnh"]),
    DictWord("音楽", "おんがく", "noun", "n5", "âm nhạc", ["nhạc"]),
    DictWord("時間", "じかん", "noun", "n5", "thời gian", ["giờ"]),
    DictWord("今日", "きょう", "noun", "n5", "hôm nay", []),
    DictWord("明日", "あした", "noun", "n5", "ngày mai", ["hôm sau", "ngày hôm sau"]),
    DictWord("昨日", "きのう", "noun", "n5", "hôm qua", []),
    DictWord("朝", "あさ", "noun", "n5", "buổi sáng", ["sáng"]),
    DictWord("昼", "ひる", "noun", "n5", "buổi trưa", ["trưa"]),
    DictWord("夜", "よる", "noun", "n5", "buổi tối", ["tối", "đêm"]),
    DictWord("名前", "なまえ", "noun", "n5", "tên", ["họ tên", "danh tính"]),
    DictWord("日本語", "にほんご", "noun", "n5", "tiếng Nhật", ["tiếng Nhật Bản"]),
    DictWord("英語", "えいご", "noun", "n5", "tiếng Anh", []),
    DictWord("国", "くに", "noun", "n5", "đất nước", ["quốc gia", "nước"]),
    DictWord("仕事", "しごと", "noun", "n5", "công việc", ["việc làm", "nghề nghiệp"]),
    DictWord("お金", "おかね", "noun", "n5", "tiền", ["tiền bạc"]),
    DictWord("店", "みせ", "noun", "n5", "cửa hàng", ["tiệm", "shop"]),
    DictWord("駅", "えき", "noun", "n5", "nhà ga", ["ga tàu", "ga xe lửa"]),
    DictWord("病院", "びょういん", "noun", "n5", "bệnh viện", []),
    DictWord("天気", "てんき", "noun", "n5", "thời tiết", []),
    DictWord("山", "やま", "noun", "n5", "núi", []),
    DictWord("川", "かわ", "noun", "n5", "sông", []),
    DictWord("海", "うみ", "noun", "n5", "biển", ["đại dương"]),
    DictWord("公園", "こうえん", "noun", "n5", "công viên", []),
    DictWord("食べ物", "たべもの", "noun", "n5", "đồ ăn", ["thức ăn", "ẩm thực"]),
    DictWord("飲み物", "のみもの", "noun", "n5", "đồ uống", ["thức uống"]),
    DictWord("水", "みず", "noun", "n5", "nước", []),
    DictWord("電話", "でんわ", "noun", "n5", "điện thoại", []),
    DictWord("テレビ", "てれび", "noun", "n5", "tivi", ["ti vi", "truyền hình"]),
    DictWord("犬", "いぬ", "noun", "n5", "con chó", ["chó"]),
    DictWord("猫", "ねこ", "noun", "n5", "con mèo", ["mèo"]),
    DictWord("花", "はな", "noun", "n5", "hoa", ["bông hoa"]),
    DictWord("木", "き", "noun", "n5", "cây", ["cây cối"]),
    DictWord("道", "みち", "noun", "n5", "con đường", ["đường", "đường đi"]),
    DictWord("空", "そら", "noun", "n5", "bầu trời", ["trời"]),
    DictWord("雨", "あめ", "noun", "n5", "mưa", []),
    DictWord("雪", "ゆき", "noun", "n5", "tuyết", []),
    DictWord("子供", "こども", "noun", "n5", "trẻ em", ["trẻ con", "con cái"]),
    DictWord("男", "おとこ", "noun", "n5", "đàn ông", ["nam giới"]),
    DictWord("女", "おんな", "noun", "n5", "phụ nữ", ["đàn bà", "nữ giới"]),
    DictWord("部屋", "へや", "noun", "n5", "phòng", ["căn phòng"]),
    DictWord("学校", "がっこう", "noun", "n5", "trường học", ["trường"]),
]

# =========================================================================
# NOUNS — N4
# =========================================================================
N4_NOUNS: list[DictWord] = [
    DictWord("意味", "いみ", "noun", "n4", "ý nghĩa", ["nghĩa"]),
    DictWord("理由", "りゆう", "noun", "n4", "lý do", ["nguyên nhân"]),
    DictWord("問題", "もんだい", "noun", "n4", "vấn đề", ["bài toán", "câu hỏi"]),
    DictWord("答え", "こたえ", "noun", "n4", "câu trả lời", ["đáp án"]),
    DictWord("例", "れい", "noun", "n4", "ví dụ", []),
    DictWord("形", "かたち", "noun", "n4", "hình dạng", ["hình", "hình thức"]),
    DictWord("色", "いろ", "noun", "n4", "màu sắc", ["màu"]),
    DictWord("計画", "けいかく", "noun", "n4", "kế hoạch", ["dự án"]),
    DictWord("予定", "よてい", "noun", "n4", "lịch trình", ["kế hoạch", "dự định"]),
    DictWord("準備", "じゅんび", "noun", "n4", "sự chuẩn bị", ["chuẩn bị"]),
    DictWord("連絡", "れんらく", "noun", "n4", "liên lạc", ["liên hệ"]),
    DictWord("会議", "かいぎ", "noun", "n4", "cuộc họp", ["buổi họp"]),
    DictWord("試験", "しけん", "noun", "n4", "kỳ thi", ["bài kiểm tra", "thi cử"]),
    DictWord("成績", "せいせき", "noun", "n4", "điểm số", ["thành tích", "kết quả học tập"]),
    DictWord("授業", "じゅぎょう", "noun", "n4", "buổi học", ["bài học", "lớp học"]),
    DictWord("宿題", "しゅくだい", "noun", "n4", "bài tập về nhà", []),
    DictWord("趣味", "しゅみ", "noun", "n4", "sở thích", []),
    DictWord("旅行", "りょこう", "noun", "n4", "du lịch", ["chuyến đi"]),
    DictWord("住所", "じゅうしょ", "noun", "n4", "địa chỉ", []),
    DictWord("経験", "けいけん", "noun", "n4", "kinh nghiệm", ["trải nghiệm"]),
    DictWord("場所", "ばしょ", "noun", "n4", "địa điểm", ["nơi", "chỗ"]),
    DictWord("ニュース", "にゅーす", "noun", "n4", "tin tức", ["tin", "thời sự"]),
    DictWord("情報", "じょうほう", "noun", "n4", "thông tin", []),
    DictWord("病気", "びょうき", "noun", "n4", "bệnh tật", ["bệnh"]),
    DictWord("薬", "くすり", "noun", "n4", "thuốc", []),
    DictWord("医者", "いしゃ", "noun", "n4", "bác sĩ", []),
    DictWord("交通", "こうつう", "noun", "n4", "giao thông", []),
    DictWord("地図", "ちず", "noun", "n4", "bản đồ", []),
    DictWord("番号", "ばんごう", "noun", "n4", "số", ["con số", "số hiệu"]),
    DictWord("写真", "しゃしん", "noun", "n4", "ảnh", ["hình ảnh"]),
    DictWord("電気", "でんき", "noun", "n4", "điện", []),
    DictWord("空港", "くうこう", "noun", "n4", "sân bay", []),
    DictWord("橋", "はし", "noun", "n4", "cây cầu", ["cầu"]),
    DictWord("建物", "たてもの", "noun", "n4", "tòa nhà", ["công trình"]),
    DictWord("台所", "だいどころ", "noun", "n4", "bếp", ["nhà bếp"]),
    DictWord("試合", "しあい", "noun", "n4", "trận đấu", ["thi đấu"]),
    DictWord("選手", "せんしゅ", "noun", "n4", "vận động viên", ["cầu thủ", "tuyển thủ"]),
    DictWord("結婚", "けっこん", "noun", "n4", "kết hôn", ["đám cưới", "hôn nhân"]),
    DictWord("生活", "せいかつ", "noun", "n4", "cuộc sống", ["sinh hoạt"]),
    DictWord("文化", "ぶんか", "noun", "n4", "văn hóa", []),
    DictWord("習慣", "しゅうかん", "noun", "n4", "thói quen", ["tập quán"]),
    DictWord("食事", "しょくじ", "noun", "n4", "bữa ăn", ["ăn uống"]),
    DictWord("料理", "りょうり", "noun", "n4", "món ăn", ["nấu ăn", "ẩm thực"]),
    DictWord("運動", "うんどう", "noun", "n4", "vận động", ["thể dục", "luyện tập"]),
    DictWord("機会", "きかい", "noun", "n4", "cơ hội", ["dịp"]),
    DictWord("方法", "ほうほう", "noun", "n4", "phương pháp", ["cách", "cách thức"]),
    DictWord("声", "こえ", "noun", "n4", "giọng nói", ["tiếng nói", "giọng"]),
    DictWord("説明", "せつめい", "noun", "n4", "giải thích", ["thuyết minh"]),
    DictWord("理解", "りかい", "noun", "n4", "sự hiểu biết", ["hiểu"]),
    DictWord("記念", "きねん", "noun", "n4", "kỷ niệm", []),
    DictWord("材料", "ざいりょう", "noun", "n4", "nguyên liệu", ["vật liệu"]),
    DictWord("注意", "ちゅうい", "noun", "n4", "chú ý", ["lưu ý", "cẩn thận"]),
    DictWord("注文", "ちゅうもん", "noun", "n4", "gọi món", ["đặt hàng"]),
    DictWord("予約", "よやく", "noun", "n4", "đặt chỗ", ["đặt trước", "đặt phòng"]),
    DictWord("紹介", "しょうかい", "noun", "n4", "giới thiệu", []),
    DictWord("挨拶", "あいさつ", "noun", "n4", "chào hỏi", ["lời chào"]),
    DictWord("感謝", "かんしゃ", "noun", "n4", "lòng biết ơn", ["cảm ơn", "biết ơn"]),
    DictWord("野菜", "やさい", "noun", "n4", "rau củ", ["rau"]),
    DictWord("果物", "くだもの", "noun", "n4", "trái cây", ["hoa quả"]),
    DictWord("服", "ふく", "noun", "n4", "quần áo", ["trang phục"]),
]

# =========================================================================
# NOUNS — N3
# =========================================================================
N3_NOUNS: list[DictWord] = [
    DictWord("気持ち", "きもち", "noun", "n3", "cảm xúc", ["cảm giác", "tâm trạng"]),
    DictWord("感情", "かんじょう", "noun", "n3", "tình cảm", ["cảm xúc"]),
    DictWord("性格", "せいかく", "noun", "n3", "tính cách", ["cá tính"]),
    DictWord("才能", "さいのう", "noun", "n3", "tài năng", ["năng khiếu"]),
    DictWord("能力", "のうりょく", "noun", "n3", "năng lực", ["khả năng"]),
    DictWord("知識", "ちしき", "noun", "n3", "kiến thức", []),
    DictWord("記憶", "きおく", "noun", "n3", "ký ức", ["trí nhớ"]),
    DictWord("夢", "ゆめ", "noun", "n3", "giấc mơ", ["ước mơ", "mơ ước"]),
    DictWord("目標", "もくひょう", "noun", "n3", "mục tiêu", []),
    DictWord("目的", "もくてき", "noun", "n3", "mục đích", []),
    DictWord("希望", "きぼう", "noun", "n3", "hi vọng", ["hy vọng", "mong muốn"]),
    DictWord("不安", "ふあん", "noun", "n3", "lo lắng", ["lo âu", "bất an"]),
    DictWord("心配", "しんぱい", "noun", "n3", "sự lo lắng", ["lo ngại"]),
    DictWord("悩み", "なやみ", "noun", "n3", "nỗi lo", ["băn khoăn", "khó khăn"]),
    DictWord("原因", "げんいん", "noun", "n3", "nguyên nhân", ["lý do"]),
    DictWord("結果", "けっか", "noun", "n3", "kết quả", ["hậu quả"]),
    DictWord("影響", "えいきょう", "noun", "n3", "ảnh hưởng", ["tác động"]),
    DictWord("変化", "へんか", "noun", "n3", "sự thay đổi", ["biến đổi"]),
    DictWord("成長", "せいちょう", "noun", "n3", "sự trưởng thành", ["phát triển", "lớn lên"]),
    DictWord("関係", "かんけい", "noun", "n3", "mối quan hệ", ["liên quan"]),
    DictWord("社会", "しゃかい", "noun", "n3", "xã hội", []),
    DictWord("歴史", "れきし", "noun", "n3", "lịch sử", []),
    DictWord("伝統", "でんとう", "noun", "n3", "truyền thống", []),
    DictWord("規則", "きそく", "noun", "n3", "quy tắc", ["quy định", "nội quy"]),
    DictWord("法律", "ほうりつ", "noun", "n3", "luật pháp", ["pháp luật"]),
    DictWord("政治", "せいじ", "noun", "n3", "chính trị", []),
    DictWord("経済", "けいざい", "noun", "n3", "kinh tế", []),
    DictWord("環境", "かんきょう", "noun", "n3", "môi trường", []),
    DictWord("自然", "しぜん", "noun", "n3", "thiên nhiên", ["tự nhiên"]),
    DictWord("科学", "かがく", "noun", "n3", "khoa học", []),
    DictWord("技術", "ぎじゅつ", "noun", "n3", "kỹ thuật", ["công nghệ"]),
    DictWord("医学", "いがく", "noun", "n3", "y học", ["y khoa"]),
    DictWord("職業", "しょくぎょう", "noun", "n3", "nghề nghiệp", ["công việc"]),
    DictWord("収入", "しゅうにゅう", "noun", "n3", "thu nhập", ["lương"]),
    DictWord("貯金", "ちょきん", "noun", "n3", "tiết kiệm", ["tiền để dành"]),
    DictWord("費用", "ひよう", "noun", "n3", "chi phí", ["tiền", "kinh phí"]),
    DictWord("事故", "じこ", "noun", "n3", "tai nạn", ["sự cố"]),
    DictWord("事件", "じけん", "noun", "n3", "sự kiện", ["vụ việc"]),
    DictWord("確認", "かくにん", "noun", "n3", "xác nhận", ["kiểm tra"]),
    DictWord("利用", "りよう", "noun", "n3", "sử dụng", ["dùng"]),
    DictWord("案内", "あんない", "noun", "n3", "hướng dẫn", ["giới thiệu"]),
    DictWord("礼儀", "れいぎ", "noun", "n3", "lễ phép", ["lịch sự", "phép tắc"]),
    DictWord("批判", "ひはん", "noun", "n3", "phê phán", ["chỉ trích", "chê"]),
    DictWord("特徴", "とくちょう", "noun", "n3", "đặc điểm", ["đặc trưng"]),
    DictWord("理想", "りそう", "noun", "n3", "lý tưởng", []),
    DictWord("現実", "げんじつ", "noun", "n3", "thực tế", ["hiện thực"]),
    DictWord("様子", "ようす", "noun", "n3", "tình hình", ["vẻ ngoài", "tình trạng"]),
    DictWord("状況", "じょうきょう", "noun", "n3", "tình huống", ["hoàn cảnh"]),
    DictWord("季節", "きせつ", "noun", "n3", "mùa", []),
    DictWord("動物", "どうぶつ", "noun", "n3", "động vật", ["con vật", "thú vật"]),
    DictWord("植物", "しょくぶつ", "noun", "n3", "thực vật", ["cây cỏ"]),
    DictWord("財布", "さいふ", "noun", "n3", "ví tiền", ["ví"]),
    DictWord("荷物", "にもつ", "noun", "n3", "hành lý", ["đồ đạc"]),
    DictWord("上司", "じょうし", "noun", "n3", "cấp trên", ["sếp", "lãnh đạo"]),
    DictWord("部下", "ぶか", "noun", "n3", "cấp dưới", ["nhân viên dưới quyền"]),
    DictWord("比較", "ひかく", "noun", "n3", "so sánh", []),
    DictWord("申し込み", "もうしこみ", "noun", "n3", "đăng ký", ["đăng ký tham gia"]),
    DictWord("気候", "きこう", "noun", "n3", "khí hậu", []),
    DictWord("投資", "とうし", "noun", "n3", "đầu tư", []),
    DictWord("借金", "しゃっきん", "noun", "n3", "nợ", ["nợ nần"]),
    DictWord("発展", "はってん", "noun", "n3", "sự phát triển", ["phát triển"]),
    DictWord("想像", "そうぞう", "noun", "n3", "trí tưởng tượng", ["tưởng tượng"]),
    DictWord("地位", "ちい", "noun", "n3", "địa vị", ["vị trí", "vị thế"]),
    DictWord("謝罪", "しゃざい", "noun", "n3", "sự xin lỗi", ["xin lỗi"]),
    DictWord("賞", "しょう", "noun", "n3", "giải thưởng", ["giải"]),
    DictWord("魚", "さかな", "noun", "n3", "cá", []),
    DictWord("部長", "ぶちょう", "noun", "n3", "trưởng phòng", ["giám đốc bộ phận"]),
    DictWord("店長", "てんちょう", "noun", "n3", "quản lý cửa hàng", ["chủ tiệm"]),
    DictWord("社長", "しゃちょう", "noun", "n3", "giám đốc", ["chủ tịch công ty"]),
    DictWord("お客さん", "おきゃくさん", "noun", "n3", "khách hàng", ["khách"]),
    DictWord("世代", "せだい", "noun", "n3", "thế hệ", []),
    DictWord("地域", "ちいき", "noun", "n3", "địa khu", ["khu vực", "địa phương"]),
    DictWord("仲間", "なかま", "noun", "n3", "bạn cùng nhóm", ["đồng nghiệp", "đồng đội"]),
    DictWord("代表", "だいひょう", "noun", "n3", "đại diện", []),
    DictWord("表現", "ひょうげん", "noun", "n3", "cách diễn đạt", ["biểu hiện"]),
    DictWord("言語", "げんご", "noun", "n3", "ngôn ngữ", []),
    DictWord("文章", "ぶんしょう", "noun", "n3", "đoạn văn", ["bài viết", "câu văn"]),
    DictWord("内容", "ないよう", "noun", "n3", "nội dung", []),
]

# =========================================================================
# NOUNS — N2
# =========================================================================
N2_NOUNS: list[DictWord] = [
    DictWord("制度", "せいど", "noun", "n2", "chế độ", ["hệ thống"]),
    DictWord("条件", "じょうけん", "noun", "n2", "điều kiện", []),
    DictWord("規模", "きぼ", "noun", "n2", "quy mô", []),
    DictWord("程度", "ていど", "noun", "n2", "mức độ", ["trình độ"]),
    DictWord("傾向", "けいこう", "noun", "n2", "xu hướng", ["khuynh hướng"]),
    DictWord("原則", "げんそく", "noun", "n2", "nguyên tắc", []),
    DictWord("方針", "ほうしん", "noun", "n2", "chính sách", ["hướng đi", "đường lối"]),
    DictWord("主張", "しゅちょう", "noun", "n2", "lập luận", ["quan điểm", "ý kiến"]),
    DictWord("意見", "いけん", "noun", "n2", "ý kiến", ["quan điểm"]),
    DictWord("提案", "ていあん", "noun", "n2", "đề xuất", ["kiến nghị"]),
    DictWord("解決", "かいけつ", "noun", "n2", "giải quyết", ["giải pháp"]),
    DictWord("対応", "たいおう", "noun", "n2", "ứng phó", ["xử lý", "đối phó"]),
    DictWord("手段", "しゅだん", "noun", "n2", "phương tiện", ["cách thức"]),
    DictWord("効果", "こうか", "noun", "n2", "hiệu quả", ["tác dụng"]),
    DictWord("被害", "ひがい", "noun", "n2", "thiệt hại", ["tổn thất"]),
    DictWord("損害", "そんがい", "noun", "n2", "thiệt hại tài sản", ["tổn thất"]),
    DictWord("支出", "ししゅつ", "noun", "n2", "chi tiêu", ["chi phí"]),
    DictWord("貿易", "ぼうえき", "noun", "n2", "thương mại", ["buôn bán"]),
    DictWord("輸出", "ゆしゅつ", "noun", "n2", "xuất khẩu", []),
    DictWord("輸入", "ゆにゅう", "noun", "n2", "nhập khẩu", []),
    DictWord("産業", "さんぎょう", "noun", "n2", "công nghiệp", ["ngành công nghiệp"]),
    DictWord("農業", "のうぎょう", "noun", "n2", "nông nghiệp", []),
    DictWord("工業", "こうぎょう", "noun", "n2", "kỹ nghệ", ["công nghiệp"]),
    DictWord("商業", "しょうぎょう", "noun", "n2", "thương nghiệp", ["thương mại"]),
    DictWord("政策", "せいさく", "noun", "n2", "chính sách", []),
    DictWord("改善", "かいぜん", "noun", "n2", "cải thiện", ["cải tiến"]),
    DictWord("支援", "しえん", "noun", "n2", "hỗ trợ", ["giúp đỡ"]),
    DictWord("確保", "かくほ", "noun", "n2", "đảm bảo", ["giữ vững"]),
    DictWord("維持", "いじ", "noun", "n2", "duy trì", ["giữ gìn"]),
    DictWord("制限", "せいげん", "noun", "n2", "giới hạn", ["hạn chế"]),
    DictWord("規制", "きせい", "noun", "n2", "quy định", ["kiểm soát", "hạn chế"]),
    DictWord("禁止", "きんし", "noun", "n2", "cấm đoán", ["cấm"]),
    DictWord("許可", "きょか", "noun", "n2", "cho phép", ["sự cho phép"]),
    DictWord("義務", "ぎむ", "noun", "n2", "nghĩa vụ", ["bổn phận"]),
    DictWord("権利", "けんり", "noun", "n2", "quyền lợi", ["quyền"]),
    DictWord("責任", "せきにん", "noun", "n2", "trách nhiệm", []),
    DictWord("信頼", "しんらい", "noun", "n2", "sự tin tưởng", ["tin cậy"]),
    DictWord("評価", "ひょうか", "noun", "n2", "đánh giá", []),
    DictWord("課題", "かだい", "noun", "n2", "nhiệm vụ", ["bài toán", "vấn đề"]),
    DictWord("基準", "きじゅん", "noun", "n2", "tiêu chuẩn", []),
    DictWord("需要", "じゅよう", "noun", "n2", "nhu cầu", []),
    DictWord("供給", "きょうきゅう", "noun", "n2", "cung cấp", []),
    DictWord("競争", "きょうそう", "noun", "n2", "cạnh tranh", []),
    DictWord("協力", "きょうりょく", "noun", "n2", "hợp tác", ["cộng tác"]),
    DictWord("連携", "れんけい", "noun", "n2", "phối hợp", ["liên kết"]),
    DictWord("分析", "ぶんせき", "noun", "n2", "phân tích", []),
    DictWord("調査", "ちょうさ", "noun", "n2", "điều tra", ["khảo sát", "nghiên cứu"]),
    DictWord("研究", "けんきゅう", "noun", "n2", "nghiên cứu", []),
    DictWord("開発", "かいはつ", "noun", "n2", "phát triển", ["khai phát"]),
    DictWord("製品", "せいひん", "noun", "n2", "sản phẩm", []),
    DictWord("品質", "ひんしつ", "noun", "n2", "chất lượng", []),
    DictWord("価格", "かかく", "noun", "n2", "giá cả", ["giá"]),
    DictWord("市場", "しじょう", "noun", "n2", "thị trường", []),
    DictWord("消費", "しょうひ", "noun", "n2", "tiêu thụ", []),
    DictWord("生産", "せいさん", "noun", "n2", "sản xuất", []),
    DictWord("輸送", "ゆそう", "noun", "n2", "vận chuyển", ["chuyên chở"]),
    DictWord("通信", "つうしん", "noun", "n2", "truyền thông", ["liên lạc"]),
    DictWord("心理", "しんり", "noun", "n2", "tâm lý", []),
    DictWord("意識", "いしき", "noun", "n2", "ý thức", ["nhận thức"]),
    DictWord("印象", "いんしょう", "noun", "n2", "ấn tượng", []),
    DictWord("雰囲気", "ふんいき", "noun", "n2", "bầu không khí", ["không khí"]),
    DictWord("表情", "ひょうじょう", "noun", "n2", "nét mặt", ["biểu cảm"]),
    DictWord("反応", "はんのう", "noun", "n2", "phản ứng", []),
    DictWord("判断", "はんだん", "noun", "n2", "phán đoán", ["đánh giá", "quyết định"]),
    DictWord("決定", "けってい", "noun", "n2", "quyết định", []),
    DictWord("選択", "せんたく", "noun", "n2", "lựa chọn", ["chọn lựa"]),
    DictWord("交流", "こうりゅう", "noun", "n2", "giao lưu", ["trao đổi"]),
    DictWord("統計", "とうけい", "noun", "n2", "thống kê", []),
    DictWord("割合", "わりあい", "noun", "n2", "tỷ lệ", ["tỉ lệ"]),
    DictWord("規格", "きかく", "noun", "n2", "tiêu chuẩn", ["quy cách"]),
    DictWord("手順", "てじゅん", "noun", "n2", "trình tự", ["quy trình", "bước"]),
]

# =========================================================================
# NOUNS — N1
# =========================================================================
N1_NOUNS: list[DictWord] = [
    DictWord("概念", "がいねん", "noun", "n1", "khái niệm", []),
    DictWord("原理", "げんり", "noun", "n1", "nguyên lý", ["nguyên tắc"]),
    DictWord("理念", "りねん", "noun", "n1", "lý tưởng", ["lý niệm"]),
    DictWord("思想", "しそう", "noun", "n1", "tư tưởng", []),
    DictWord("哲学", "てつがく", "noun", "n1", "triết học", []),
    DictWord("論理", "ろんり", "noun", "n1", "logic", ["lô-gic"]),
    DictWord("価値観", "かちかん", "noun", "n1", "hệ giá trị", ["quan niệm giá trị"]),
    DictWord("世界観", "せかいかん", "noun", "n1", "thế giới quan", []),
    DictWord("観点", "かんてん", "noun", "n1", "quan điểm", ["góc nhìn"]),
    DictWord("視点", "してん", "noun", "n1", "góc nhìn", ["quan điểm"]),
    DictWord("立場", "たちば", "noun", "n1", "lập trường", ["vị trí", "quan điểm"]),
    DictWord("姿勢", "しせい", "noun", "n1", "thái độ", ["tư thế"]),
    DictWord("態度", "たいど", "noun", "n1", "thái độ", []),
    DictWord("戦略", "せんりゃく", "noun", "n1", "chiến lược", []),
    DictWord("対策", "たいさく", "noun", "n1", "biện pháp", ["giải pháp", "đối sách"]),
    DictWord("予防", "よぼう", "noun", "n1", "phòng ngừa", ["phòng tránh"]),
    DictWord("保護", "ほご", "noun", "n1", "bảo vệ", []),
    DictWord("権威", "けんい", "noun", "n1", "quyền uy", ["uy tín"]),
    DictWord("権力", "けんりょく", "noun", "n1", "quyền lực", []),
    DictWord("公正", "こうせい", "noun", "n1", "công bằng", []),
    DictWord("格差", "かくさ", "noun", "n1", "khoảng cách", ["chênh lệch"]),
    DictWord("矛盾", "むじゅん", "noun", "n1", "mâu thuẫn", []),
    DictWord("偏見", "へんけん", "noun", "n1", "định kiến", ["thành kiến"]),
    DictWord("差別", "さべつ", "noun", "n1", "phân biệt đối xử", ["kỳ thị"]),
    DictWord("平等", "びょうどう", "noun", "n1", "bình đẳng", []),
    DictWord("組織", "そしき", "noun", "n1", "tổ chức", []),
    DictWord("秩序", "ちつじょ", "noun", "n1", "trật tự", []),
    DictWord("混乱", "こんらん", "noun", "n1", "hỗn loạn", []),
    DictWord("危機", "きき", "noun", "n1", "khủng hoảng", []),
    DictWord("緊張", "きんちょう", "noun", "n1", "căng thẳng", []),
    DictWord("安定", "あんてい", "noun", "n1", "ổn định", []),
    DictWord("持続", "じぞく", "noun", "n1", "duy trì", ["bền vững"]),
    DictWord("克服", "こくふく", "noun", "n1", "vượt qua", []),
    DictWord("挑戦", "ちょうせん", "noun", "n1", "thử thách", []),
    DictWord("革新", "かくしん", "noun", "n1", "cách tân", ["đổi mới"]),
    DictWord("創造", "そうぞう", "noun", "n1", "sáng tạo", []),
    DictWord("革命", "かくめい", "noun", "n1", "cách mạng", []),
    DictWord("普及", "ふきゅう", "noun", "n1", "phổ biến", []),
    DictWord("展開", "てんかい", "noun", "n1", "triển khai", ["phát triển"]),
    DictWord("拡大", "かくだい", "noun", "n1", "mở rộng", []),
    DictWord("廃止", "はいし", "noun", "n1", "bãi bỏ", ["xóa bỏ"]),
    DictWord("違反", "いはん", "noun", "n1", "vi phạm", []),
    DictWord("裁判", "さいばん", "noun", "n1", "xét xử", ["tòa án"]),
    DictWord("判決", "はんけつ", "noun", "n1", "phán quyết", ["bản án"]),
    DictWord("促進", "そくしん", "noun", "n1", "thúc đẩy", ["khuyến khích"]),
    DictWord("統合", "とうごう", "noun", "n1", "thống nhất", ["tích hợp"]),
    DictWord("遵守", "じゅんしゅ", "noun", "n1", "tuân thủ", []),
    DictWord("把握", "はあく", "noun", "n1", "nắm bắt", ["hiểu rõ"]),
    DictWord("整備", "せいび", "noun", "n1", "sắp xếp", ["bảo trì"]),
    DictWord("抑制", "よくせい", "noun", "n1", "kiềm chế", ["hạn chế"]),
    DictWord("縮小", "しゅくしょう", "noun", "n1", "thu hẹp", []),
]

# =========================================================================
# ADJECTIVES — N5 (adj-i + adj-na)
# =========================================================================
N5_ADJ: list[DictWord] = [
    # adj-i
    DictWord("いい", "いい", "adj_i", "n5", "tốt", ["hay", "tốt lành"]),
    DictWord("悪い", "わるい", "adj_i", "n5", "xấu", ["tồi", "tệ"]),
    DictWord("大きい", "おおきい", "adj_i", "n5", "to lớn", ["lớn", "to"]),
    DictWord("小さい", "ちいさい", "adj_i", "n5", "nhỏ bé", ["nhỏ", "bé"]),
    DictWord("新しい", "あたらしい", "adj_i", "n5", "mới", []),
    DictWord("古い", "ふるい", "adj_i", "n5", "cũ", ["cũ kỹ"]),
    DictWord("高い", "たかい", "adj_i", "n5", "cao / đắt", ["đắt tiền", "đắt"]),
    DictWord("安い", "やすい", "adj_i", "n5", "rẻ", ["rẻ tiền"]),
    DictWord("暑い", "あつい", "adj_i", "n5", "nóng", ["nóng bức"]),
    DictWord("寒い", "さむい", "adj_i", "n5", "lạnh", []),
    DictWord("暖かい", "あたたかい", "adj_i", "n5", "ấm áp", ["ấm"]),
    DictWord("涼しい", "すずしい", "adj_i", "n5", "mát mẻ", ["mát"]),
    DictWord("難しい", "むずかしい", "adj_i", "n5", "khó", ["khó khăn"]),
    DictWord("易しい", "やさしい", "adj_i", "n5", "dễ", ["dễ dàng"]),
    DictWord("楽しい", "たのしい", "adj_i", "n5", "vui", ["vui vẻ", "thú vị"]),
    DictWord("面白い", "おもしろい", "adj_i", "n5", "thú vị", ["hay", "hấp dẫn", "buồn cười"]),
    DictWord("忙しい", "いそがしい", "adj_i", "n5", "bận rộn", ["bận"]),
    DictWord("速い", "はやい", "adj_i", "n5", "nhanh", []),
    DictWord("遅い", "おそい", "adj_i", "n5", "chậm", ["trễ"]),
    DictWord("近い", "ちかい", "adj_i", "n5", "gần", []),
    DictWord("遠い", "とおい", "adj_i", "n5", "xa", []),
    DictWord("長い", "ながい", "adj_i", "n5", "dài", []),
    DictWord("短い", "みじかい", "adj_i", "n5", "ngắn", []),
    # adj-na
    DictWord("好き", "すき", "adj_na", "n5", "thích", ["yêu thích"]),
    DictWord("嫌い", "きらい", "adj_na", "n5", "ghét", ["không thích"]),
    DictWord("きれい", "きれい", "adj_na", "n5", "đẹp / sạch", ["xinh đẹp", "sạch sẽ"]),
    DictWord("静か", "しずか", "adj_na", "n5", "yên tĩnh", ["yên lặng"]),
    DictWord("にぎやか", "にぎやか", "adj_na", "n5", "nhộn nhịp", ["ồn ào", "sầm uất"]),
    DictWord("元気", "げんき", "adj_na", "n5", "khỏe mạnh", ["khỏe", "năng động"]),
    DictWord("便利", "べんり", "adj_na", "n5", "tiện lợi", ["thuận tiện"]),
]

# =========================================================================
# ADJECTIVES — N4
# =========================================================================
N4_ADJ: list[DictWord] = [
    # adj-i
    DictWord("嬉しい", "うれしい", "adj_i", "n4", "vui mừng", ["hạnh phúc", "vui"]),
    DictWord("悲しい", "かなしい", "adj_i", "n4", "buồn", ["đau buồn"]),
    DictWord("怖い", "こわい", "adj_i", "n4", "đáng sợ", ["sợ hãi", "ghê"]),
    DictWord("痛い", "いたい", "adj_i", "n4", "đau", []),
    DictWord("眠い", "ねむい", "adj_i", "n4", "buồn ngủ", []),
    DictWord("寂しい", "さびしい", "adj_i", "n4", "cô đơn", ["cô quạnh"]),
    DictWord("珍しい", "めずらしい", "adj_i", "n4", "hiếm có", ["lạ", "độc đáo"]),
    DictWord("かわいい", "かわいい", "adj_i", "n4", "đáng yêu", ["dễ thương", "cute"]),
    DictWord("正しい", "ただしい", "adj_i", "n4", "đúng", ["chính xác", "đúng đắn"]),
    DictWord("危ない", "あぶない", "adj_i", "n4", "nguy hiểm", []),
    DictWord("優しい", "やさしい", "adj_i", "n4", "tốt bụng", ["hiền lành", "dịu dàng"]),
    DictWord("重い", "おもい", "adj_i", "n4", "nặng", []),
    DictWord("軽い", "かるい", "adj_i", "n4", "nhẹ", []),
    DictWord("細かい", "こまかい", "adj_i", "n4", "tỉ mỉ", ["chi tiết"]),
    # adj-na
    DictWord("丁寧", "ていねい", "adj_na", "n4", "lịch sự", ["cẩn thận", "lịch thiệp"]),
    DictWord("必要", "ひつよう", "adj_na", "n4", "cần thiết", ["cần"]),
    DictWord("特別", "とくべつ", "adj_na", "n4", "đặc biệt", []),
    DictWord("普通", "ふつう", "adj_na", "n4", "bình thường", ["thường"]),
    DictWord("幸せ", "しあわせ", "adj_na", "n4", "hạnh phúc", []),
    DictWord("有名", "ゆうめい", "adj_na", "n4", "nổi tiếng", ["danh tiếng"]),
    DictWord("親切", "しんせつ", "adj_na", "n4", "thân thiện", ["tử tế", "ân cần"]),
    DictWord("大事", "だいじ", "adj_na", "n4", "quan trọng", []),
    DictWord("重要", "じゅうよう", "adj_na", "n4", "quan trọng", ["thiết yếu"]),
    DictWord("素直", "すなお", "adj_na", "n4", "thật thà", ["ngoan ngoãn"]),
    DictWord("真剣", "しんけん", "adj_na", "n4", "nghiêm túc", ["chân thành"]),
    DictWord("複雑", "ふくざつ", "adj_na", "n4", "phức tạp", []),
    DictWord("明らか", "あきらか", "adj_na", "n4", "rõ ràng", ["hiển nhiên"]),
    DictWord("積極的", "せっきょくてき", "adj_na", "n4", "tích cực", []),
    DictWord("消極的", "しょうきょくてき", "adj_na", "n4", "tiêu cực", ["thụ động"]),
    DictWord("自由", "じゆう", "adj_na", "n4", "tự do", []),
]

# =========================================================================
# ADJECTIVES — N3
# =========================================================================
N3_ADJ: list[DictWord] = [
    DictWord("恥ずかしい", "はずかしい", "adj_i", "n3", "xấu hổ", ["ngại", "mắc cỡ"]),
    DictWord("羨ましい", "うらやましい", "adj_i", "n3", "ghen tị", ["đố kỵ", "thèm"]),
    DictWord("苦しい", "くるしい", "adj_i", "n3", "đau khổ", ["khổ sở"]),
    DictWord("辛い", "つらい", "adj_i", "n3", "vất vả", ["gian khó", "khó khăn"]),
    DictWord("懐かしい", "なつかしい", "adj_i", "n3", "hoài niệm", ["nhớ nhung"]),
    DictWord("温かい", "あたたかい", "adj_i", "n3", "ấm áp (tình cảm)", ["ấm lòng"]),
    DictWord("冷たい", "つめたい", "adj_i", "n3", "lạnh lùng", ["lạnh nhạt", "lạnh"]),
    DictWord("激しい", "はげしい", "adj_i", "n3", "dữ dội", ["mãnh liệt", "mạnh mẽ"]),
    DictWord("素晴らしい", "すばらしい", "adj_i", "n3", "tuyệt vời", ["xuất sắc"]),
    DictWord("怪しい", "あやしい", "adj_i", "n3", "đáng ngờ", ["khả nghi"]),
    DictWord("鋭い", "するどい", "adj_i", "n3", "sắc bén", ["nhạy bén", "nhọn"]),
    DictWord("深い", "ふかい", "adj_i", "n3", "sâu sắc", ["sâu"]),
    DictWord("硬い", "かたい", "adj_i", "n3", "cứng", []),
    DictWord("柔らかい", "やわらかい", "adj_i", "n3", "mềm", ["mềm mại"]),
    DictWord("汚い", "きたない", "adj_i", "n3", "bẩn thỉu", ["dơ bẩn", "dơ"]),
    # adj-na
    DictWord("安全", "あんぜん", "adj_na", "n3", "an toàn", []),
    DictWord("危険", "きけん", "adj_na", "n3", "nguy hiểm", []),
    DictWord("正直", "しょうじき", "adj_na", "n3", "thành thật", ["thật thà", "trung thực"]),
    DictWord("熱心", "ねっしん", "adj_na", "n3", "nhiệt tình", ["tận tâm"]),
    DictWord("不便", "ふべん", "adj_na", "n3", "bất tiện", []),
    DictWord("迷惑", "めいわく", "adj_na", "n3", "phiền toái", ["phiền hà"]),
    DictWord("大胆", "だいたん", "adj_na", "n3", "táo bạo", ["can đảm"]),
    DictWord("慎重", "しんちょう", "adj_na", "n3", "thận trọng", ["cẩn thận"]),
    DictWord("冷静", "れいせい", "adj_na", "n3", "bình tĩnh", ["điềm tĩnh"]),
    DictWord("残念", "ざんねん", "adj_na", "n3", "đáng tiếc", ["tiếc"]),
    DictWord("不思議", "ふしぎ", "adj_na", "n3", "kỳ diệu", ["lạ", "huyền bí"]),
    DictWord("清潔", "せいけつ", "adj_na", "n3", "sạch sẽ", ["vệ sinh"]),
    DictWord("孤独", "こどく", "adj_na", "n3", "cô đơn", ["cô lẻ"]),
    DictWord("独特", "どくとく", "adj_na", "n3", "độc đáo", ["đặc biệt"]),
    DictWord("柔軟", "じゅうなん", "adj_na", "n3", "linh hoạt", ["mềm dẻo"]),
    DictWord("有効", "ゆうこう", "adj_na", "n3", "có hiệu lực", ["hiệu quả"]),
    DictWord("公平", "こうへい", "adj_na", "n3", "công bằng", []),
    DictWord("上品", "じょうひん", "adj_na", "n3", "thanh lịch", ["tao nhã"]),
    DictWord("健全", "けんぜん", "adj_na", "n3", "lành mạnh", []),
    DictWord("穏やか", "おだやか", "adj_na", "n3", "nhẹ nhàng", ["điềm tĩnh", "bình tĩnh"]),
]

# =========================================================================
# ADJECTIVES — N2
# =========================================================================
N2_ADJ: list[DictWord] = [
    DictWord("厳しい", "きびしい", "adj_i", "n2", "nghiêm khắc", ["khắt khe"]),
    DictWord("凄い", "すごい", "adj_i", "n2", "kinh ngạc", ["tuyệt vời", "ghê", "ấn tượng"]),
    DictWord("賢い", "かしこい", "adj_i", "n2", "thông minh", ["khôn ngoan"]),
    DictWord("微妙", "びみょう", "adj_na", "n2", "tinh tế", ["tế nhị"]),
    DictWord("効率的", "こうりつてき", "adj_na", "n2", "hiệu quả", []),
    DictWord("具体的", "ぐたいてき", "adj_na", "n2", "cụ thể", []),
    DictWord("抽象的", "ちゅうしょうてき", "adj_na", "n2", "trừu tượng", []),
    DictWord("適切", "てきせつ", "adj_na", "n2", "phù hợp", ["thích hợp"]),
    DictWord("合理的", "ごうりてき", "adj_na", "n2", "hợp lý", []),
    DictWord("現実的", "げんじつてき", "adj_na", "n2", "thực tế", []),
    DictWord("理想的", "りそうてき", "adj_na", "n2", "lý tưởng", []),
    DictWord("客観的", "きゃっかんてき", "adj_na", "n2", "khách quan", []),
    DictWord("主観的", "しゅかんてき", "adj_na", "n2", "chủ quan", []),
    DictWord("徹底的", "てっていてき", "adj_na", "n2", "triệt để", []),
    DictWord("専門的", "せんもんてき", "adj_na", "n2", "chuyên môn", []),
    DictWord("曖昧", "あいまい", "adj_na", "n2", "mơ hồ", ["không rõ ràng"]),
    DictWord("明確", "めいかく", "adj_na", "n2", "rõ ràng", ["chắc chắn"]),
    DictWord("包括的", "ほうかつてき", "adj_na", "n2", "toàn diện", []),
    DictWord("一方的", "いっぽうてき", "adj_na", "n2", "một chiều", ["đơn phương"]),
    DictWord("独自", "どくじ", "adj_na", "n2", "độc lập", ["riêng"]),
    DictWord("精密", "せいみつ", "adj_na", "n2", "chính xác", ["tinh tế"]),
    DictWord("不適切", "ふてきせつ", "adj_na", "n2", "không phù hợp", []),
    DictWord("相互的", "そうごてき", "adj_na", "n2", "qua lại lẫn nhau", []),
    DictWord("積極的", "せっきょくてき", "adj_na", "n2", "tích cực chủ động", []),
]

# =========================================================================
# ADJECTIVES — N1
# =========================================================================
N1_ADJ: list[DictWord] = [
    DictWord("根本的", "こんぽんてき", "adj_na", "n1", "căn bản", ["cơ bản"]),
    DictWord("本質的", "ほんしつてき", "adj_na", "n1", "bản chất", []),
    DictWord("抜本的", "ばっぽんてき", "adj_na", "n1", "triệt để", ["tận gốc"]),
    DictWord("画期的", "かっきてき", "adj_na", "n1", "đột phá", ["tiên phong"]),
    DictWord("先進的", "せんしんてき", "adj_na", "n1", "tiên tiến", []),
    DictWord("革新的", "かくしんてき", "adj_na", "n1", "đổi mới", ["cách mạng"]),
    DictWord("保守的", "ほしゅてき", "adj_na", "n1", "bảo thủ", []),
    DictWord("進歩的", "しんぽてき", "adj_na", "n1", "tiến bộ", []),
    DictWord("批判的", "ひはんてき", "adj_na", "n1", "phê phán", ["phản biện"]),
    DictWord("創造的", "そうぞうてき", "adj_na", "n1", "sáng tạo", []),
    DictWord("建設的", "けんせつてき", "adj_na", "n1", "xây dựng", ["tích cực"]),
    DictWord("象徴的", "しょうちょうてき", "adj_na", "n1", "biểu tượng", []),
    DictWord("形式的", "けいしきてき", "adj_na", "n1", "hình thức", []),
    DictWord("実質的", "じっしつてき", "adj_na", "n1", "thực chất", ["thực tế"]),
    DictWord("理論的", "りろんてき", "adj_na", "n1", "lý luận", []),
    DictWord("経験的", "けいけんてき", "adj_na", "n1", "thực nghiệm", []),
    DictWord("壮大", "そうだい", "adj_na", "n1", "hùng vĩ", []),
    DictWord("緻密", "ちみつ", "adj_na", "n1", "tỉ mỉ chặt chẽ", []),
    DictWord("甚大", "じんだい", "adj_na", "n1", "rất lớn", ["to lớn"]),
    DictWord("顕著", "けんちょ", "adj_na", "n1", "nổi bật", ["rõ ràng"]),
]

# =========================================================================
# AGGREGATED POOLS
# =========================================================================
ALL_NOUNS: list[DictWord] = (
    N5_NOUNS + N4_NOUNS + N3_NOUNS + N2_NOUNS + N1_NOUNS
)

ALL_ADJ: list[DictWord] = (
    N5_ADJ + N4_ADJ + N3_ADJ + N2_ADJ + N1_ADJ
)

# Difficulty buckets (nouns + adjectives only)
EASY_NOUNS_ADJ: list[DictWord] = N5_NOUNS + N4_NOUNS + N5_ADJ + N4_ADJ
NORMAL_NOUNS_ADJ: list[DictWord] = N3_NOUNS + N3_ADJ
HARD_NOUNS_ADJ: list[DictWord] = N2_NOUNS + N1_NOUNS + N2_ADJ + N1_ADJ


def _dict_verb_to_word(v: "DictVerb") -> DictWord:  # type: ignore[name-defined]
    """Convert a DictVerb to a DictWord for unified vocab pool."""
    return DictWord(
        word=v.verb,
        reading=v.reading,
        word_type="verb",
        jlpt=v.level,
        meaning_vi=v.meaning_vi,
        synonyms_vi=[],
    )


# =========================================================================
# UNIFIED VOCAB POOL (verbs + nouns + adjectives)
# Lazy import to avoid circular imports — call build_all_vocab_words() once.
# =========================================================================
_ALL_VOCAB_WORDS: list[DictWord] | None = None
_EASY_VOCAB: list[DictWord] | None = None
_NORMAL_VOCAB: list[DictWord] | None = None
_HARD_VOCAB: list[DictWord] | None = None


def _ensure_vocab_words() -> None:
    global _ALL_VOCAB_WORDS, _EASY_VOCAB, _NORMAL_VOCAB, _HARD_VOCAB
    if _ALL_VOCAB_WORDS is not None:
        return
    from app.domains.reflex.dictionary_pool import (
        ALL_DICT_VERBS,
        EASY_VERBS,
        HARD_VERBS,
        NORMAL_VERBS,
    )
    verb_words = [_dict_verb_to_word(v) for v in ALL_DICT_VERBS]
    easy_verb_words = [_dict_verb_to_word(v) for v in EASY_VERBS]
    normal_verb_words = [_dict_verb_to_word(v) for v in NORMAL_VERBS]
    hard_verb_words = [_dict_verb_to_word(v) for v in HARD_VERBS]

    _ALL_VOCAB_WORDS = verb_words + ALL_NOUNS + ALL_ADJ
    _EASY_VOCAB = easy_verb_words + EASY_NOUNS_ADJ
    _NORMAL_VOCAB = normal_verb_words + NORMAL_NOUNS_ADJ
    _HARD_VOCAB = hard_verb_words + HARD_NOUNS_ADJ


def get_all_vocab_words() -> list[DictWord]:
    _ensure_vocab_words()
    assert _ALL_VOCAB_WORDS is not None
    return _ALL_VOCAB_WORDS


def get_easy_vocab() -> list[DictWord]:
    _ensure_vocab_words()
    assert _EASY_VOCAB is not None
    return _EASY_VOCAB


def get_normal_vocab() -> list[DictWord]:
    _ensure_vocab_words()
    assert _NORMAL_VOCAB is not None
    return _NORMAL_VOCAB


def get_hard_vocab() -> list[DictWord]:
    _ensure_vocab_words()
    assert _HARD_VOCAB is not None
    return _HARD_VOCAB
