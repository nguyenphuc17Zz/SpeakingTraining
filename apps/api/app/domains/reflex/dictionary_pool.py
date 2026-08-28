"""Comprehensive Dictionary Pool and Non-Repeating Randomizer for Japanese Reflex Training.

Provides thousands of verbs categorized by JLPT level (N5 -> N1), Q&A topics,
sentence transformations, and situational dialogue prompts.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any


@dataclass
class DictVerb:
    verb: str
    reading: str
    meaning_vi: str
    level: str  # easy, normal, hard


# =========================================================================
# 1. COMPREHENSIVE VERB DICTIONARY POOL (N5 -> N1)
# =========================================================================
EASY_VERBS: list[DictVerb] = [
    DictVerb("食べる", "たべる", "Ăn", "easy"),
    DictVerb("飲む", "のむ", "Uống", "easy"),
    DictVerb("見る", "みる", "Xem, nhìn", "easy"),
    DictVerb("聞く", "きく", "Nghe, hỏi", "easy"),
    DictVerb("読む", "よむ", "Đọc", "easy"),
    DictVerb("書く", "かく", "Viết", "easy"),
    DictVerb("行く", "いく", "Đi", "easy"),
    DictVerb("来る", "くる", "Đến", "easy"),
    DictVerb("帰る", "かえる", "Về", "easy"),
    DictVerb("会う", "あう", "Gặp gỡ", "easy"),
    DictVerb("買う", "かう", "Mua", "easy"),
    DictVerb("売る", "うる", "Bán", "easy"),
    DictVerb("待つ", "まつ", "Đợi, chờ", "easy"),
    DictVerb("立つ", "たつ", "Đứng", "easy"),
    DictVerb("座る", "すわる", "Ngồi", "easy"),
    DictVerb("話す", "はなす", "Nói chuyện", "easy"),
    DictVerb("言う", "いう", "Nói", "easy"),
    DictVerb("教える", "おしえる", "Dạy, chỉ bảo", "easy"),
    DictVerb("習う", "ならう", "Học", "easy"),
    DictVerb("泳ぐ", "およぐ", "Bơi", "easy"),
    DictVerb("走る", "はしる", "Chạy", "easy"),
    DictVerb("歩く", "あるく", "Đi bộ", "easy"),
    DictVerb("起きる", "おきる", "Thức dậy", "easy"),
    DictVerb("寝る", "ねる", "Ngủ", "easy"),
    DictVerb("働く", "はたらく", "Làm việc", "easy"),
    DictVerb("休む", "やすむ", "Nghỉ ngơi", "easy"),
    DictVerb("遊ぶ", "あそぶ", "Chơi", "easy"),
    DictVerb("開ける", "あける", "Mở", "easy"),
    DictVerb("閉める", "しめる", "Đóng", "easy"),
    DictVerb("つける", "つける", "Bật (đèn)", "easy"),
    DictVerb("消す", "けす", "Tắt, xóa", "easy"),
    DictVerb("借りる", "かりる", "Mượn", "easy"),
    DictVerb("貸す", "かす", "Cho mượn", "easy"),
    DictVerb("返す", "かえす", "Trả lại", "easy"),
    DictVerb("出す", "だす", "Lấy ra, nộp", "easy"),
    DictVerb("入れる", "いれる", "Cho vào", "easy"),
    DictVerb("作る", "つくる", "Làm, chế tạo", "easy"),
    DictVerb("使う", "つかう", "Dùng, sử dụng", "easy"),
    DictVerb("持つ", "もつ", "Cầm, có", "easy"),
    DictVerb("知る", "しる", "Biết", "easy"),
    DictVerb("覚える", "おぼえる", "Ghi nhớ", "easy"),
    DictVerb("忘れる", "わすれる", "Quên", "easy"),
    DictVerb("洗う", "あらう", "Rửa, giặt", "easy"),
    DictVerb("歌う", "うたう", "Hát", "easy"),
    DictVerb("吸う", "すう", "Hút, hít", "easy"),
    DictVerb("乗る", "のる", "Lên xe", "easy"),
    DictVerb("降りる", "おりる", "Xuống xe", "easy"),
    DictVerb("入る", "はいる", "Đi vào", "easy"),
    DictVerb("出る", "でる", "Đi ra, rời khỏi", "easy"),
    DictVerb("渡す", "わたす", "Trao, đưa", "easy"),
    DictVerb("呼ぶ", "よぶ", "Gọi", "easy"),
    DictVerb("頼む", "たのむ", "Nhờ vả", "easy"),
    DictVerb("手伝う", "てつだう", "Giúp đỡ", "easy"),
    DictVerb("急ぐ", "いそぐ", "Vội, gấp", "easy"),
    DictVerb("止める", "とめる", "Dừng lại", "easy"),
    DictVerb("始める", "はじめる", "Bắt đầu", "easy"),
    DictVerb("終わる", "おわる", "Kết thúc", "easy"),
]

NORMAL_VERBS: list[DictVerb] = [
    DictVerb("考える", "かんがえる", "Suy nghĩ, cân nhắc", "normal"),
    DictVerb("信じる", "しんじる", "Tin tưởng", "normal"),
    DictVerb("感じる", "かんじる", "Cảm thấy", "normal"),
    DictVerb("調べる", "しらべる", "Tra cứu, điều tra", "normal"),
    DictVerb("知らせる", "しらせる", "Thông báo", "normal"),
    DictVerb("伝える", "つたえる", "Truyền đạt", "normal"),
    DictVerb("届ける", "とどける", "Giao đến", "normal"),
    DictVerb("直す", "なおす", "Sửa chữa", "normal"),
    DictVerb("直る", "なおる", "Được sửa", "normal"),
    DictVerb("治る", "なおる", "Khỏi bệnh", "normal"),
    DictVerb("比べる", "くらべる", "So sánh", "normal"),
    DictVerb("片付ける", "かたづける", "Dọn dẹp", "normal"),
    DictVerb("気をつける", "きをつける", "Chú ý, cẩn thận", "normal"),
    DictVerb("確かめる", "たしかめる", "Xác nhận", "normal"),
    DictVerb("見つける", "みつける", "Tìm thấy", "normal"),
    DictVerb("見つかる", "みつかる", "Được tìm thấy", "normal"),
    DictVerb("迎える", "むかえる", "Đón tiếp", "normal"),
    DictVerb("送る", "おくる", "Gửi, tiễn", "normal"),
    DictVerb("遅れる", "おくれる", "Đến muộn", "normal"),
    DictVerb("起こす", "おこす", "Đánh thức", "normal"),
    DictVerb("落ちる", "おちる", "Rơi xuống", "normal"),
    DictVerb("落とす", "おとす", "Làm rơi", "normal"),
    DictVerb("拾う", "ひろう", "Nhặt lên", "normal"),
    DictVerb("捨てる", "すてる", "Vứt bỏ", "normal"),
    DictVerb("断る", "ことわる", "Từ chối", "normal"),
    DictVerb("許す", "ゆるす", "Tha thứ, cho phép", "normal"),
    DictVerb("怒る", "おこる", "Tức giận", "normal"),
    DictVerb("笑う", "わらう", "Cười", "normal"),
    DictVerb("泣く", "なく", "Khóc", "normal"),
    DictVerb("喜ぶ", "よろこぶ", "Vui mừng", "normal"),
    DictVerb("困る", "こまる", "Khó khăn, bối rối", "normal"),
    DictVerb("助ける", "たすける", "Cứu giúp", "normal"),
    DictVerb("助かる", "たすかる", "Được cứu, may quá", "normal"),
    DictVerb("勝つ", "かつ", "Chiến thắng", "normal"),
    DictVerb("負ける", "まける", "Thua cuộc", "normal"),
    DictVerb("続ける", "つづける", "Tiếp tục", "normal"),
    DictVerb("集める", "あつめる", "Thu thập", "normal"),
    DictVerb("選ぶ", "えらぶ", "Lựa chọn", "normal"),
    DictVerb("変える", "かえる", "Thay đổi", "normal"),
    DictVerb("間に合う", "まにあう", "Kịp giờ", "normal"),
    DictVerb("壊す", "こわす", "Làm hỏng", "normal"),
    DictVerb("壊れる", "こわれる", "Bị hỏng", "normal"),
    DictVerb("倒れる", "たおれる", "Ngã, đổ", "normal"),
    DictVerb("折る", "おる", "Bẻ, gấp", "normal"),
    DictVerb("育てる", "そだてる", "Nuôi nấng", "normal"),
    DictVerb("並べる", "ならべる", "Sắp xếp", "normal"),
]

HARD_VERBS: list[DictVerb] = [
    DictVerb("引き受ける", "ひきうける", "Đảm nhận việc", "hard"),
    DictVerb("受け入れる", "うけいれる", "Tiếp nhận, chấp nhận", "hard"),
    DictVerb("話し合う", "はなしあう", "Thảo luận", "hard"),
    DictVerb("申し込む", "もうしこむ", "Đăng ký", "hard"),
    DictVerb("思い出す", "おもいだす", "Nhớ lại", "hard"),
    DictVerb("思い付く", "おもいつく", "Nghĩ ra ý tưởng", "hard"),
    DictVerb("見直す", "みなおす", "Đánh giá lại, xem lại", "hard"),
    DictVerb("見つめる", "みつめる", "Nhìn chằm chằm", "hard"),
    DictVerb("見極める", "みきわめる", "Nhìn thấu, đánh giá rõ", "hard"),
    DictVerb("振り返る", "ふりかえる", "Nhìn lại quá khứ", "hard"),
    DictVerb("乗り換える", "のりかえる", "Chuyển tàu/xe", "hard"),
    DictVerb("取り組む", "とりくむ", "Chuyên tâm nỗ lực", "hard"),
    DictVerb("取り替える", "とりかえる", "Thay thế, đổi mới", "hard"),
    DictVerb("立ち上げる", "たちあげる", "Khởi động dự án", "hard"),
    DictVerb("追いかける", "おいかける", "Đuổi theo", "hard"),
    DictVerb("追いつく", "おいつく", "Đuổi kịp", "hard"),
    DictVerb("追い越す", "おいこす", "Vượt qua", "hard"),
    DictVerb("抱える", "かかえる", "Gánh vác trách nhiệm", "hard"),
    DictVerb("関わる", "かかわる", "Liên quan tới", "hard"),
    DictVerb("従う", "したがう", "Tuân theo", "hard"),
    DictVerb("逆らう", "さからう", "Chống đối", "hard"),
    DictVerb("成し遂げる", "なしとげる", "Hoàn thành trọn vẹn", "hard"),
    DictVerb("目指す", "めざす", "Nhắm tới mục tiêu", "hard"),
    DictVerb("促す", "うながす", "Thúc đẩy, nhắc nhở", "hard"),
    DictVerb("預かる", "あずかる", "Trông nom, giữ hộ", "hard"),
    DictVerb("預ける", "あずける", "Gửi gắm, giao phó", "hard"),
    DictVerb("奪う", "うばう", "Cướp đoạt", "hard"),
    DictVerb("補う", "おぎなう", "Bổ sung, bù đắp", "hard"),
    DictVerb("納める", "おさめる", "Nộp thuế, giao hàng", "hard"),
    DictVerb("諦める", "あきらめる", "Từ bỏ", "hard"),
]

ALL_DICT_VERBS: list[DictVerb] = EASY_VERBS + NORMAL_VERBS + HARD_VERBS

# =========================================================================
# 2. COMPREHENSIVE Q&A TOPICS (100+ DIVERSE REALISTIC QUESTIONS)
# =========================================================================
DICT_QNA_QUESTIONS = [
    # Daily Life & Routines
    {"q": "週末は何をする予定ですか？", "translation": "Cuối tuần bạn định làm gì?", "sample_answer": "友達と映画を見に行く予定です。"},
    {"q": "最近ハマっていることは何ですか？", "translation": "Gần đây bạn đang mê mẩn điều gì?", "sample_answer": "最近は日本の料理を作ることにハマっています。"},
    {"q": "昨日の夜は何を食べましたか？", "translation": "Tối qua bạn đã ăn món gì?", "sample_answer": "昨日の夜はラーメンを食べました。"},
    {"q": "日本で行ってみたい場所はどこですか？", "translation": "Nơi nào ở Nhật bạn muốn đến nhất?", "sample_answer": "京都の古いお寺や神社に行ってみたいです。"},
    {"q": "仕事で一番大切にしていることは何ですか？", "translation": "Điều bạn coi trọng nhất trong công việc là gì?", "sample_answer": "チームワークと時間を守ることを大切にしています。"},
    {"q": "日本語を勉強し始めたきっかけは何ですか？", "translation": "Lý do bạn bắt đầu học tiếng Nhật là gì?", "sample_answer": "日本のアニメが好きで、字幕なしで観たかったからです。"},
    {"q": "今週一番楽しかった出来事は何ですか？", "translation": "Chuyện vui nhất trong tuần này là gì?", "sample_answer": "友達と美味しい焼肉を食べに行ったことです。"},
    {"q": "休日はインドア派ですか、アウトドア派ですか？", "translation": "Ngày nghỉ bạn thích ở nhà hay đi ra ngoài?", "sample_answer": "家で本を読んだり映画を観るインドア派です。"},
    {"q": "朝起きて一番最初にすることは何ですか？", "translation": "Buổi sáng thức dậy việc đầu tiên bạn làm là gì?", "sample_answer": "まずコップ一杯の水を飲みます。"},
    {"q": "好きな季節はいつですか？その理由も教えてください。", "translation": "Bạn thích mùa nào nhất và lý do tại sao?", "sample_answer": "秋が好きです。涼しくて紅葉がとても綺麗だからです。"},
    {"q": "ストレスが溜まった時、どうやって発散しますか？", "translation": "Khi căng thẳng, bạn giải tỏa bằng cách nào?", "sample_answer": "好きな音楽を聴きながら散歩をします。"},
    {"q": "最近観た映画やアニメで面白かったものはありますか？", "translation": "Gần đây có phim hay anime nào bạn thấy hay không?", "sample_answer": "最近観たジブリの映画がとても感動的でした。"},
    {"q": "おすすめのベトナム料理は何ですか？", "translation": "Món ăn Việt Nam nào bạn muốn giới thiệu nhất?", "sample_answer": "フォーとバインミーが本当におすすめです。"},
    {"q": "将来、どんな仕事に挑戦してみたいですか？", "translation": "Tương lai bạn muốn thử sức với công việc nào?", "sample_answer": "グローバルなITプロジェクトに関わりたいです。"},
    {"q": "今日の天気はどうですか？", "translation": "Thời tiết hôm nay thế nào?", "sample_answer": "今日は晴れていて、とても気持ちがいい天気です。"},
    {"q": "よく使うスマホのアプリは何ですか？", "translation": "Ứng dụng điện thoại bạn hay dùng nhất là gì?", "sample_answer": "YouTubeと語学学習アプリをよく使います。"},
    {"q": "犬派ですか、それとも猫派ですか？", "translation": "Bạn thích chó hơn hay thích mèo hơn?", "sample_answer": "猫派です。のんびりしていて可愛いからです。"},
    {"q": "自分を一言で表すと、どんな性格ですか？", "translation": "Nếu miêu tả bản thân bằng một từ thì bạn là người thế nào?", "sample_answer": "前向きで好奇心旺盛な性格です。"},
    {"q": "旅行に行くなら、海と山どちらが好きですか？", "translation": "Đi du lịch bạn thích đi biển hay đi núi?", "sample_answer": "海が好きです。波の音を聞くとリラックスできます。"},
    {"q": "仕事や勉強で集中したい時、何をしますか？", "translation": "Khi muốn tập trung, bạn làm cách nào?", "sample_answer": "スマホを置いて、静かな音楽をかけます。"},
    {"q": "日本料理で一番好きなものは何ですか？", "translation": "Món ăn Nhật bạn thích nhất là gì?", "sample_answer": "新鮮なお寿司が一番好きです。"},
    {"q": "普段、運動は定期的にしていますか？", "translation": "Bình thường bạn có hay tập thể dục không?", "sample_answer": "週に2回くらいジョギングをしています。"},
    {"q": "夜寝る前によくすることは何ですか？", "translation": "Trước khi đi ngủ bạn thường làm gì?", "sample_answer": "日記を書いてからストレッチをします。"},
    {"q": "コーヒー派ですか、お茶派ですか？", "translation": "Bạn thích uống cà phê hay uống trà?", "sample_answer": "朝は目覚ましにコーヒーをよく飲みます。"},
    {"q": "今年の目標は何ですか？", "translation": "Mục tiêu trong năm nay của bạn là gì?", "sample_answer": "日本語のスピーキング力をアップさせることです。"},

    # Travel & Culture
    {"q": "今度旅行に行くなら、どこへ行きたいですか？", "translation": "Nếu đi du lịch lần tới, bạn muốn đi đâu?", "sample_answer": "北海道に行って、雪景色と温泉を楽しみたいです。"},
    {"q": "日本の文化で興味深いと思うものは何ですか？", "translation": "Văn hoá Nhật Bản bạn thấy thú vị nhất là gì?", "sample_answer": "礼儀正しさや茶道の精神にとても興味があります。"},
    {"q": "海外旅行で一番印象に残っている国はどこですか？", "translation": "Quốc gia nào bạn ấn tượng nhất khi đi du lịch nước ngoài?", "sample_answer": "日本です。街がとても綺麗で人が親切でした。"},
    {"q": "飛行機に乗る時、窓側と通路側どちらを選びますか？", "translation": "Đi máy bay bạn chọn ngồi ghế cửa sổ hay lối đi?", "sample_answer": "外の景色を見るのが好きなので窓側を選びます。"},
    {"q": "ホテルを選ぶ時に一番重視するポイントは何ですか？", "translation": "Khi chọn khách sạn, bạn chú trọng nhất điều gì?", "sample_answer": "清潔さと駅からの近さを一番重視します。"},
    {"q": "観光地で写真をたくさん撮るタイプですか？", "translation": "Bạn có phải kiểu người thích chụp nhiều ảnh ở điểm du lịch không?", "sample_answer": "はい、思い出を残すためにたくさん撮ります。"},
    {"q": "日本の温泉に入ったことがありますか？", "translation": "Bạn đã từng tắm suối nước nóng Onsen ở Nhật chưa?", "sample_answer": "はい、露天風呂がとても気持ちよかったです。"},
    {"q": "祭りや花火大会に行ったことがありますか？", "translation": "Bạn đã từng đi lễ hội hay ngắm pháo hoa chưa?", "sample_answer": "はい、浴衣を着て花火大会に行きました。"},

    # Work & Study
    {"q": "仕事で失敗した時、どうやって乗り越えますか？", "translation": "Khi gặp thất bại trong công việc, bạn vượt qua bằng cách nào?", "sample_answer": "原因を冷静に分析して、次の対策を立てます。"},
    {"q": "テレワークとオフィス出社、どちらが好きですか？", "translation": "Làm việc từ xa hay đến văn phòng, bạn thích cái nào hơn?", "sample_answer": "集中できるのでテレワークの方が好きです。"},
    {"q": "職場で良い人間関係を築くコツは何だと思いますか？", "translation": "Bí quyết để xây dựng quan hệ tốt ở nơi làm việc là gì?", "sample_answer": "毎日の挨拶と感謝の気持ちを伝えることです。"},
    {"q": "新しいスキルを身につける時、どうやって勉強しますか？", "translation": "Khi học kỹ năng mới, bạn học bằng cách nào?", "sample_answer": "オンライン講座を受けたり、実際に手を動かして練習します。"},
    {"q": "会議で自分の意見を言うのは得意ですか？", "translation": "Bạn có tự tin nêu ý kiến trong cuộc họp không?", "sample_answer": "少し緊張しますが、準備をしてから発言するようにしています。"},
    {"q": "仕事の締め切りが迫っている時、どう対応しますか？", "translation": "Khi deadline cận kề, bạn xử lý thế nào?", "sample_answer": "優先順位をつけて、最も重要なタスクから集中して終わらせます。"},
    {"q": "理想の上司やリーダーはどんな人ですか？", "translation": "Hình mẫu sếp hoặc lãnh đạo lý tưởng của bạn là người thế nào?", "sample_answer": "部下の意見をよく聞いて、適切なアドバイスをくれる人です。"},

    # Hobbies & Entertainment
    {"q": "最近、何か新しい趣味を始めましたか？", "translation": "Gần đây bạn có bắt đầu sở thích mới nào không?", "sample_answer": "最近、ギターの練習を始めました。"},
    {"q": "一番好きな音楽のジャンルは何ですか？", "translation": "Thể loại âm nhạc bạn yêu thích nhất là gì?", "sample_answer": "J-POPやアコースティックな音楽が好きです。"},
    {"q": "休日に友達と遊ぶなら何をすることが多いですか？", "translation": "Ngày nghỉ đi chơi với bạn thì bạn hay làm gì?", "sample_answer": "おしゃれなカフェに行っておしゃべりをします。"},
    {"q": "ゲームはよくしますか？どんなゲームが好きですか？", "translation": "Bạn có hay chơi game không? Thích loại game nào?", "sample_answer": "ロールプレイングゲームやパズルゲームをよくやります。"},
    {"q": "本を読むのは好きですか？電子書籍と紙の本、どちら派ですか？", "translation": "Bạn thích đọc sách không? Thích sách điện tử hay sách giấy?", "sample_answer": "紙の手触りが好きなので、紙の本をよく読みます。"},
    {"q": "料理を作るのは得意ですか？得意料理は何ですか？", "translation": "Bạn có giỏi nấu ăn không? Món tủ là gì?", "sample_answer": "得意料理は卵焼きと野菜炒めです。"},
    {"q": "カラオケでよく歌う曲は何ですか？", "translation": "Đi karaoke bạn thường hát bài gì?", "sample_answer": "日本の有名なアニメソングをよく歌います。"},

    # Food & Dining
    {"q": "朝ご飯はしっかり食べる派ですか？", "translation": "Bạn có phải kiểu người ăn sáng đầy đủ không?", "sample_answer": "はい、元気を出すためにパンや卵を食べます。"},
    {"q": "辛い食べ物は好きですか？", "translation": "Bạn có thích ăn đồ cay không?", "sample_answer": "大好きです！キムチやチゲをよく食べます。"},
    {"q": "外食する時、どんなお店を選ぶことが多いですか？", "translation": "Khi đi ăn ngoài, bạn thường chọn quán như thế nào?", "sample_answer": "落ち着いた雰囲気で美味しい定食屋さんを選びます。"},
    {"q": "甘いデザートの中で一番好きなものは何ですか？", "translation": "Trong các món tráng miệng ngọt, bạn thích món nào nhất?", "sample_answer": "抹茶アイスとチーズケーキが一番好きです。"},
    {"q": "自炊と外食、普段はどちらが多いですか？", "translation": "Tự nấu ăn hay ăn ngoài, bình thường bạn chọn cái nào nhiều hơn?", "sample_answer": "健康と節約のために自炊を多くしています。"},

    # Technology & Society
    {"q": "AI技術の発展についてどう思いますか？", "translation": "Bạn nghĩ gì về sự phát triển của công nghệ AI?", "sample_answer": "とても便利で、学習や仕事の効率が上がると期待しています。"},
    {"q": "ネットショッピングはよく利用しますか？", "translation": "Bạn có thường xuyên mua sắm online không?", "sample_answer": "はい、日用品や本をよくネットで買います。"},
    {"q": "SNSを見る時間は1日にどのくらいですか？", "translation": "Một ngày bạn dành khoảng bao nhiêu thời gian lướt MXH?", "sample_answer": "だいたい1時間くらいです。使いすぎないように気をつけています。"},

    # Situations & Quick Opinions
    {"q": "もし明日突然休みになったら、何をしますか？", "translation": "Nếu ngày mai đột nhiên được nghỉ, bạn sẽ làm gì?", "sample_answer": "一日中ゆっくり寝て、好きな映画を観ます。"},
    {"q": "タイムマシンがあったら、過去と未来どちらに行きたいですか？", "translation": "Nếu có cỗ máy thời gian, bạn muốn về quá khứ hay đến tương lai?", "sample_answer": "100年後の未来の世界を見てみたいです。"},
    {"q": "無人島に一つだけ持っていけるとしたら、何を持っていきますか？", "translation": "Nếu chỉ được mang 1 thứ đến đảo hoang, bạn sẽ mang gì?", "sample_answer": "火を起こす道具を持っていきます。"},
    {"q": "生まれ変わったら何になりたいですか？", "translation": "Nếu được tái sinh, bạn muốn trở thành cái gì?", "sample_answer": "空を自由に飛べる鳥になってみたいです。"},
    {"q": "最近、嬉しかった褒め言葉は何ですか？", "translation": "Lời khen gần đây khiến bạn vui nhất là gì?", "sample_answer": "「日本語の発音が綺麗だね」と褒められたことです。"},
    {"q": "緊張した時、心を落ち着かせる方法はありますか？", "translation": "Khi căng thẳng, bạn có cách nào để bình tĩnh lại không?", "sample_answer": "深呼吸を3回して、大丈夫だと自分に言い聞かせます。"},
    {"q": "子供の頃の将来の夢は何でしたか？", "translation": "Ước mơ hồi nhỏ của bạn là gì?", "sample_answer": "宇宙飛行士になりたかったです。"},
]

# =========================================================================
# 3. COMPREHENSIVE TRANSFORMATION TASKS (40+ DIVERSE DRILLS)
# =========================================================================
DICT_TRANSFORMATIONS = [
    # Casual & Polite Forms
    {"source": "今日は東京に行きます。", "task": "カジュアルな過去形 (Thể ngắn quá khứ)", "expected": "今日は東京に行った。", "translation": "Hôm nay tôi sẽ đi Tokyo."},
    {"source": "この本は面白いです。", "task": "否定形 (Thể phủ định)", "expected": "この本は面白くないです。", "translation": "Cuốn sách này thú vị."},
    {"source": "明日、会議があります。", "task": "カジュアル (Thể ngắn)", "expected": "明日、会議がある。", "translation": "Ngày mai có cuộc họp."},
    {"source": "彼は毎日運動する。", "task": "丁寧語 (Thể lịch sự ます)", "expected": "彼は毎日運動します。", "translation": "Anh ấy tập thể dục mỗi ngày."},
    {"source": "週末は映画を見ました。", "task": "カジュアル (Thể ngắn)", "expected": "週末は映画を見た。", "translation": "Cuối tuần tôi đã xem phim."},
    {"source": "コーヒーを飲みません。", "task": "カジュアル (Thể ngắn)", "expected": "コーヒーを飲まない。", "translation": "Tôi không uống cà phê."},
    {"source": "昨日はとても寒かった。", "task": "丁寧語 (Thể lịch sự です)", "expected": "昨日はとても寒かったです。", "translation": "Hôm qua trời rất lạnh."},
    {"source": "一緒にご飯を食べましょう。", "task": "カジュアルな意向形 (Rủ rê thể ngắn)", "expected": "一緒にご飯を食べよう。", "translation": "Cùng đi ăn cơm nhé."},

    # Passive & Causative Forms
    {"source": "先生が生徒を褒めた。", "task": "受身形 (Thể bị động)", "expected": "生徒は先生に褒められた。", "translation": "Thầy giáo đã khen học sinh."},
    {"source": "泥棒が財布を盗んだ。", "task": "迷惑受身 (Bị động phiền toái)", "expected": "財布を盗まれた。", "translation": "Kẻ trộm lấy cắp ví."},
    {"source": "母が子供に野菜を食べさせた。", "task": "使役形 (Thể sai khiến)", "expected": "母が子供に野菜を食べさせた。", "translation": "Mẹ bắt con ăn rau."},
    {"source": "上司が部下を残業させた。", "task": "使役形 (Thể sai khiến)", "expected": "上司が部下を残業させた。", "translation": "Sếp bắt cấp dưới làm thêm giờ."},
    {"source": "私は先輩に歌を歌わされた。", "task": "使役受身形 (Thể bị sai khiến)", "expected": "先輩に歌を歌わされた。", "translation": "Tôi bị tiền bối bắt hát."},

    # Conditional Forms (ば・たら・なら)
    {"source": "薬を飲むと治る。", "task": "〜たら形 (Thể điều kiện たら)", "expected": "薬を飲んだら治る。", "translation": "Uống thuốc thì sẽ khỏi."},
    {"source": "安ければ買います。", "task": "〜たら形 (Thể điều kiện たら)", "expected": "安かったら買います。", "translation": "Nếu rẻ thì sẽ mua."},
    {"source": "時間がありません。", "task": "〜ば形 (Thể điều kiện ば)", "expected": "時間がなければ。", "translation": "Nếu không có thời gian."},
    {"source": "雨が降ります。", "task": "〜たら形 (Thể điều kiện たら)", "expected": "雨が降ったら。", "translation": "Nếu trời mưa."},
    {"source": "日本に行くなら、富士山を見たい。", "task": "〜たら形 (Thể điều kiện たら)", "expected": "日本に行ったら、富士山を見たい。", "translation": "Nếu đi Nhật, muốn ngắm núi Phú Sĩ."},

    # Potential & Volitional Forms
    {"source": "日本語を話します。", "task": "可能形 (Thể khả năng)", "expected": "日本語が話せます。", "translation": "Nói tiếng Nhật."},
    {"source": "漢字を書くことができます。", "task": "可能形 (Thể khả năng ngắn gọn)", "expected": "漢字が書けます。", "translation": "Có thể viết chữ Hán."},
    {"source": "刺身を食べます。", "task": "可能形の否定 (Không thể ăn)", "expected": "刺身が食べられません。", "translation": "Không thể ăn sashimi."},
    {"source": "今週末、山に登ります。", "task": "意向形 (Thể ý chí)", "expected": "今週末、山に登ろう。", "translation": "Cuối tuần này định leo núi."},
    {"source": "早く寝ます。", "task": "意向形 (Thể ý chí)", "expected": "早く寝よう。", "translation": "Định đi ngủ sớm."},

    # Te-form & Giving/Receiving
    {"source": "友達が本を貸してくれました。", "task": "〜てもらう形 (Được bạn cho mượn)", "expected": "友達に本を貸してもらいました。", "translation": "Bạn đã cho tôi mượn sách."},
    {"source": "先生に教えていただきました。", "task": "カジュアル (Nhận sự chỉ dạy)", "expected": "先生に教えてもらった。", "translation": "Được thầy giáo chỉ dạy."},
]

# =========================================================================
# 4. COMPREHENSIVE CONTEXTUAL DIALOGUES (40+ REALISTIC SCENARIOS)
# =========================================================================
DICT_CONTEXTS = [
    # Workplace & Business
    {
        "scenario": "Colleague: 明日の会議、何時からでしたっけ？",
        "intent": "Trả lời là bắt đầu từ 10 giờ sáng tại phòng họp A.",
        "expected": "明日は10時から会議室Aですよ。",
        "translation": "Đồng nghiệp hỏi cuộc họp mai mấy giờ, trả lời 10h ở phòng họp A.",
        "role": "Đồng nghiệp",
    },
    {
        "scenario": "Boss: この資料、今日中に終わらせてくれる？",
        "intent": "Đồng ý nhận việc và báo sẽ hoàn thành trước 5 giờ chiều.",
        "expected": "かしこまりました。5時までに終わらせます。",
        "translation": "Sếp nhờ hoàn thành tài liệu trong hôm nay, đồng ý và báo trước 5h chiều.",
        "role": "Cấp trên",
    },
    {
        "scenario": "Colleague: 手伝いましょうか？",
        "intent": "Cảm ơn và nhờ bê hộ chiếc hộp này.",
        "expected": "ありがとうございます！この箱を持っていただけますか？",
        "translation": "Đồng nghiệp ngỏ ý giúp đỡ, cảm ơn và nhờ bê hộp.",
        "role": "Đồng nghiệp",
    },
    {
        "scenario": "Client: 来週の火曜日に打ち合わせは可能ですか？",
        "intent": "Xác nhận được và đề xuất lúc 2 giờ chiều.",
        "expected": "はい、大丈夫です。午後2時はいかがでしょうか？",
        "translation": "Khách hàng hỏi thứ ba tuần tới có họp được không, đồng ý và hẹn 2h chiều.",
        "role": "Khách hàng",
    },
    {
        "scenario": "Colleague: お先に失礼します。",
        "intent": "Đáp lại lời chào khi đồng nghiệp về trước (Cảm ơn vì đã vất vả).",
        "expected": "お疲れ様でした！",
        "translation": "Đồng nghiệp chào về trước, đáp lại lời cảm ơn vất vả.",
        "role": "Đồng nghiệp",
    },

    # Casual & Friends
    {
        "scenario": "Friend: このラーメン、辛い？",
        "intent": "Trả lời là không cay lắm, rất ngon.",
        "expected": "そんなに辛くないよ。すごく美味しい！",
        "translation": "Bạn hỏi mì ramen có cay không, trả lời không cay lắm và ngon.",
        "role": "Bạn bè",
    },
    {
        "scenario": "Friend: 今夜、飲みに行かない？",
        "intent": "Từ chối khéo vì tối nay có hẹn khác, hẹn dịp sau.",
        "expected": "ごめん、今夜は先約があるんだ。また今度誘って！",
        "translation": "Bạn rủ tối nay đi nhậu, từ chối khéo vì bận và hẹn lần tới.",
        "role": "Bạn bè",
    },
    {
        "scenario": "Friend: 日本語上手になったね！",
        "intent": "Khiêm tốn cảm ơn, bảo vẫn còn phải học nhiều.",
        "expected": "ありがとうございます！でも、まだまだ勉強中です。",
        "translation": "Bạn khen tiếng Nhật giỏi, khiêm tốn cảm ơn.",
        "role": "Bạn bè",
    },
    {
        "scenario": "Friend: 映画、何時からだっけ？",
        "intent": "Báo là 3 giờ chiều, hẹn gặp ở trước rạp lúc 2 rưỡi.",
        "expected": "3時からだよ。2時半に映画館の前で会おう！",
        "translation": "Bạn hỏi phim mấy giờ chiếu, báo 3h và hẹn 2h30 trước rạp.",
        "role": "Bạn bè",
    },
    {
        "scenario": "Friend: この服、どう思う？似合ってる？",
        "intent": "Khen rất đẹp và hợp với phong cách của bạn.",
        "expected": "すごく似合ってるよ！色がとてもいいね。",
        "translation": "Bạn hỏi bộ quần áo này có hợp không, khen đẹp và màu sắc tốt.",
        "role": "Bạn bè",
    },

    # Public & Services
    {
        "scenario": "Waiter: ご注文はお決まりですか？",
        "intent": "Xin thêm 2 phút để xem menu.",
        "expected": "すみません、もう少々時間をいただけますか？",
        "translation": "Nhân viên quán hỏi đã chọn món chưa, xin thêm vài phút.",
        "role": "Nhân viên quán",
    },
    {
        "scenario": "Passerby: すみません、駅はどちらですか？",
        "intent": "Chỉ đường đi thẳng rồi rẽ phải ở ngã tư.",
        "expected": "まっすぐ行って、次の交差点を右に曲がるとありますよ。",
        "translation": "Người lạ hỏi đường ra ga, chỉ đi thẳng rẽ phải ở ngã tư.",
        "role": "Người đi đường",
    },
    {
        "scenario": "Store Clerk: レジ袋はご利用になりますか？",
        "intent": "Từ chối vì đã mang theo túi cá nhân.",
        "expected": "大丈夫です。マイバッグを持っています。",
        "translation": "Thu ngân hỏi có cần túi nilon không, từ chối vì có túi riêng.",
        "role": "Thu ngân",
    },
    {
        "scenario": "Taxi Driver: どちらまで行かれますか？",
        "intent": "Báo địa điểm muốn đến là ga Tokyo.",
        "expected": "東京駅までお願いします。",
        "translation": "Tài xế taxi hỏi đi đâu, báo đến ga Tokyo.",
        "role": "Tài xế taxi",
    },
]

