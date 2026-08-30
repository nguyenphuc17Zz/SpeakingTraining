"""Vocabulary Dictionary Pool for Reflex Vocabulary Mode (reflex_vocabulary).

Organized into 5 practical communicative categories:
- action_verbs: Động từ hành động & đời sống
- emotions_adj: Tính từ & Trạng thái cảm xúc
- adverbs_mimetic: Phó từ & Từ tượng thanh/tượng hình (擬音語・擬態語)
- workplace_biz: Công sở, Thương mại & Hou-Ren-So
- daily_life: Sinh hoạt, Mua sắm & Dịch vụ

Usage:
    from app.domains.reflex.vocab_pool import (
        ALL_VOCAB_WORDS, get_all_vocab_words, get_vocab_by_category, DictWord
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DictWord:
    word: str             # 連絡 / 諦める / 懐かしい
    reading: str          # れんらく / あきらめる / なつかしい
    word_type: str        # verb | noun | adj_i | adj_na | adverb
    category: str         # action_verbs | emotions_adj | adverbs_mimetic | workplace_biz | daily_life
    meaning_vi: str       # liên lạc
    synonyms_vi: list[str] = field(default_factory=list)
    collocation_ja: str = ""   # 連絡を取る
    collocation_vi: str = ""   # giữ liên lạc
    example_ja: str = ""       # 後でLINEで連絡するね！
    example_vi: str = ""       # Lát nữa mình nhắn qua LINE cho cậu nhé!
    jlpt: str = ""


# =========================================================================
# 1. ACTION VERBS (Động từ hành động & đời sống)
# =========================================================================
ACTION_VERBS: list[DictWord] = [
    DictWord("連絡する", "れんらくする", "verb", "action_verbs", "liên lạc", ["gọi điện", "nhắn tin", "thông báo"], "連絡を取る", "giữ liên lạc", "後でLINEで連絡するね！", "Lát nữa mình nhắn qua LINE cho cậu nhé!"),
    DictWord("諦める", "あきらめる", "verb", "action_verbs", "bỏ cuộc", ["từ bỏ", "thôi"], "夢を諦めない", "không từ bỏ ước mơ", "最後まで決して諦めないでください。", "Xin đừng bao giờ bỏ cuộc cho tới phút cuối cùng."),
    DictWord("案内する", "あんないする", "verb", "action_verbs", "hướng dẫn", ["dẫn đường", "chỉ đường", "giới thiệu"], "街を案内する", "dẫn đi tham quan phố", "東京の有名な場所をご案内します。", "Tôi sẽ hướng dẫn bạn tham quan những địa điểm nổi tiếng ở Tokyo."),
    DictWord("断る", "ことわる", "verb", "action_verbs", "từ chối", ["bác bỏ", "khước từ"], "誘いを断る", "từ chối lời mời", "先約があったので丁寧にお断りしました。", "Vì có hẹn trước nên tôi đã từ chối một cách lịch sự."),
    DictWord("片付ける", "かたづける", "verb", "action_verbs", "dọn dẹp", ["sắp xếp", "thu dọn"], "部屋を片付ける", "dọn dẹp phòng", "週末に部屋をきれいに片付けました。", "Cuối tuần tôi đã dọn dẹp phòng ốc thật sạch sẽ."),
    DictWord("届ける", "とどける", "verb", "action_verbs", "giao đến", ["chuyển đến", "đưa tới"], "荷物を届ける", "giao hành lý", "明日午前中に書類をお届けいたします。", "Tôi sẽ giao tài liệu đến vào sáng mai ạ."),
    DictWord("受け取る", "うけとる", "verb", "action_verbs", "nhận lấy", ["tiếp nhận", "thu nhận"], "荷物を受け取る", "nhận bưu kiện", "先ほど確かに荷物を受け取りました。", "Tôi vừa mới nhận được bưu kiện xong."),
    DictWord("振り返る", "ふりかえる", "verb", "action_verbs", "nhìn lại", ["ngẫm lại", "quay đầu nhìn"], "過去を振り返る", "nhìn lại quá khứ", "たまには自分の行動を振り返ることも大切です。", "Thỉnh thoảng nhìn nhận lại hành động của bản thân cũng rất quan trọng."),
    DictWord("思い出す", "おもいだす", "verb", "action_verbs", "nhớ ra", ["hồi tưởng", "nhớ lại"], "昔のことを思い出す", "nhớ lại chuyện xưa", "ふと子供の頃の思い出を思い出しました。", "Bất chợt tôi nhớ lại những kỷ niệm thời thơ ấu."),
    DictWord("申し込む", "もうしこむ", "verb", "action_verbs", "đăng ký", ["ứng tuyển", "ngỏ lời"], "講座に申し込む", "đăng ký khóa học", "日本語スピーキング講座に申し込みました。", "Tôi đã đăng ký khóa học luyện nói tiếng Nhật."),
    DictWord("確認する", "かくにんする", "verb", "action_verbs", "xác nhận", ["kiểm tra lại", "rà soát"], "スケジュールを確認する", "kiểm tra lịch trình", "念のためもう一度時間を確認しましょう。", "Để cho chắc chắn, chúng ta cùng kiểm tra lại giờ giấc nhé."),
    DictWord("相談する", "そうだんする", "verb", "action_verbs", "thảo luận", ["trao đổi", "xin ý kiến", "bàn bạc"], "上司に相談する", "trao đổi với cấp trên", "困ったことがあればいつでも相談してください。", "Nếu có khó khăn gì bạn cứ trao đổi với tôi bất cứ lúc nào nhé."),
    DictWord("乗り換える", "のりかえる", "verb", "action_verbs", "chuyển tuyến", ["đổi tàu", "đổi xe"], "電車を乗り換える", "đổi tàu điện", "次の駅で山手線に乗り換えます。", "Ở ga tiếp theo chúng ta sẽ chuyển sang tuyến Yamanote."),
    DictWord("遅れる", "おくれる", "verb", "action_verbs", "trễ", ["muộn", "chậm trễ"], "時間に遅れる", "đến muộn giờ", "事故で電車が15分遅れました。", "Do sự cố nên tàu đã bị trễ 15 phút."),
    DictWord("手伝う", "てつだう", "verb", "action_verbs", "giúp đỡ", ["phụ giúp", "hỗ trợ"], "仕事を手伝う", "phụ giúp công việc", "何か手伝えることがあれば言ってね。", "Có việc gì cần phụ giúp thì cứ bảo mình nhé."),
    DictWord("頼む", "たのむ", "verb", "action_verbs", "nhờ vả", ["yêu cầu", "đặt món"], "お願いを頼む", "nhờ vả một việc", "先輩に資料のチェックを頼みました。", "Tôi đã nhờ tiền bối kiểm tra giúp tập tài liệu."),
    DictWord("誘う", "さそう", "verb", "action_verbs", "rủ rê", ["mời", "rủ đi cùng"], "食事に誘う", "mời đi ăn cơm", "今夜ご飯でも食べに行かないと誘われました。", "Tôi được rủ tối nay đi ăn cơm cùng."),
    DictWord("見送る", "みおくる", "verb", "action_verbs", "tiễn", ["tiễn đưa", "hoãn lại"], "友達を見送る", "tiễn bạn bè", "空港まで友達を見送りに行きました。", "Tôi đã ra sân bay để tiễn bạn."),
    DictWord("迎える", "むかえる", "verb", "action_verbs", "đón", ["chào đón", "đón tiếp"], "お客様を迎える", "đón tiếp khách quý", "笑顔でお客様をお迎えしましょう。", "Chúng ta hãy nở nụ cười đón tiếp khách hàng thật chu đáo."),
    DictWord("片付く", "かたづく", "verb", "action_verbs", "được giải quyết", ["được dọn sạch", "xong xuôi"], "仕事が片付く", "công việc được giải quyết xong", "ようやく急ぎの仕事が片付きました。", "Cuối cùng công việc gấp cũng đã được giải quyết xong xuôi."),
]

# =========================================================================
# 2. EMOTIONS & ADJECTIVES (Tính từ & Cảm xúc)
# =========================================================================
EMOTIONS_ADJ: list[DictWord] = [
    DictWord("懐かしい", "なつかしい", "adj_i", "emotions_adj", "nhớ nhung", ["hoài niệm", "thân thương"], "懐かしい思い出", "kỷ niệm thân thương", "この曲を聴くと高校時代が懐かしいです。", "Nghe bài hát này làm tôi nhớ lại thời cấp ba thân thương."),
    DictWord("悔しい", "くやしい", "adj_i", "emotions_adj", "tiếc nuối", ["cay cú", "ấm ức"], "悔しい思いをする", "trải qua cảm giác tiếc nuối", "あと一歩で負けてしまって本当に悔しいです。", "Chỉ thua trong gang tấc nên tôi cảm thấy vô cùng tiếc nuối."),
    DictWord("面倒くさい", "めんどうくさい", "adj_i", "emotions_adj", "phiền phức", ["ngại làm", "lười"], "手続きが面倒くさい", "thủ tục phiền phức", "掃除をするのが面倒くさい時は音楽を聴きます。", "Những lúc lười dọn dẹp nhà cửa tôi thường bật nhạc nghe."),
    DictWord("怪しい", "あやしい", "adj_i", "emotions_adj", "khả nghi", ["đáng ngờ", "kỳ lạ"], "怪しい人物", "người khả nghi", "最近、近所で怪しい人を見かけました。", "Gần đây tôi thấy có người lạ khả nghi quanh khu nhà."),
    DictWord("羨ましい", "うらやましい", "adj_i", "emotions_adj", "ghen tị", ["ngưỡng mộ", "thèm được như thế"], "才能が羨ましい", "ngưỡng mộ tài năng", "日本語が流暢に話せて本当に羨ましいです！", "Bạn nói tiếng Nhật lưu loát như vậy làm mình ngưỡng mộ thật đấy!"),
    DictWord("もったいない", "もったいない", "adj_i", "emotions_adj", "lãng phí", ["uổng phí", "tiếc của"], "時間を無駄にするのはもったいない", "lãng phí thời gian thật uổng", "まだ使えるのに捨てるのはもったいないですよ。", "Đồ vẫn còn dùng tốt mà vứt đi thì lãng phí quá."),
    DictWord("恥ずかしい", "はずかしい", "adj_i", "emotions_adj", "xấu hổ", ["ngượng ngùng", "e thẹn"], "人前で恥ずかしい", "ngại ngùng trước đám đông", "人前で発表するとき少し恥ずかしかったです。", "Khi thuyết trình trước đám đông tôi cảm thấy hơi ngượng ngùng."),
    DictWord("素晴らしい", "すばらしい", "adj_i", "emotions_adj", "tuyệt vời", ["xuất sắc", "tuyệt diệu"], "素晴らしい景色", "phong cảnh tuyệt đẹp", "富士山の山頂からの眺めは本当に素晴らしかったです。", "Quang cảnh từ đỉnh núi Phú Sĩ thực sự vô cùng tuyệt vời."),
    DictWord("詳しい", "くわしい", "adj_i", "emotions_adj", "am hiểu", ["tường tận", "chi tiết"], "パソコンに詳しい", "rất rành về máy tính", "彼はITの知識がとても詳しいです。", "Anh ấy rất am hiểu và có kiến thức sâu rộng về mảng IT."),
    DictWord("険しい", "けわしい", "adj_i", "emotions_adj", "hiểm trở", ["dốc đứng", "nghiêm nghị"], "険しい山道", "đường núi hiểm trở", "山頂までの道はとても険しかったです。", "Đoạn đường leo lên đỉnh núi rất quanh co hiểm trở."),
    DictWord("頼もしい", "たのもしい", "adj_i", "emotions_adj", "đáng tin cậy", ["vững chãi", "chỗ dựa tốt"], "頼もしい後輩", "hậu bối rất đáng tin cậy", "彼はいつも冷静でとても頼もしい存在です。", "Anh ấy luôn điềm đạm và là chỗ dựa vô cùng vững chãi."),
    DictWord("惜しい", "おしい", "adj_i", "emotions_adj", "tiếc", ["suýt soát", "uổng"], "惜しいチャンス", "cơ hội suýt soát", "あと少しで満点だったのに、惜しかったです！", "Chỉ thiếu một chút xíu nữa là điểm tuyệt đối rồi, tiếc thật đấy!"),
    DictWord("苦手な", "にがてな", "adj_na", "emotions_adj", "kém", ["không giỏi", "ngại"], "早起きが苦手", "ngại dậy sớm", "私は人前で話すのが少し苦手です。", "Tôi hơi ngại khi phải phát biểu trước đông người."),
    DictWord("得意な", "とくいな", "adj_na", "emotions_adj", "giỏi", ["sở trường", "thế mạnh"], "料理が得意", "sở trường nấu ăn", "私の得意な料理はフォーです。", "Món ăn sở trường của tôi là món Phở."),
    DictWord("大切な", "たいせつな", "adj_na", "emotions_adj", "quan trọng", ["quý giá", "thiết yếu"], "大切な約束", "lời hứa quan trọng", "家族と過ごす時間は私にとって一番大切です。", "Khoảng thời gian bên gia đình là điều quan trọng nhất với tôi."),
    DictWord("新鮮な", "しんせんな", "adj_na", "emotions_adj", "tươi mới", ["tươi ngon", "trong lành"], "新鮮な魚", "cá tươi ngon", "朝市で新鮮な野菜を買ってきました。", "Tôi vừa ra chợ sớm mua được một mớ rau củ rất tươi ngon."),
    DictWord("快適な", "かいてきな", "adj_na", "emotions_adj", "thoải mái", ["dễ chịu", "tiện nghi"], "快適なホテル", "khách sạn tiện nghi thoải mái", "この部屋は日当たりが良くてとても快適です。", "Căn phòng này đón nắng tốt nên ở rất thoải mái dễ chịu."),
    DictWord("不安な", "ふあんな", "adj_na", "emotions_adj", "bất an", ["lo lắng", "lo âu"], "将来が不安", "lo lắng về tương lai", "初めての一人暮らしは少し不安でした。", "Lần đầu sống tự lập một mình tôi cảm thấy hơi lo lắng."),
]

# =========================================================================
# 3. ADVERBS & MIMETIC WORDS (Phó từ & Từ tượng thanh/hình)
# =========================================================================
ADVERBS_MIMETIC: list[DictWord] = [
    DictWord("ぺらぺら", "ぺらぺら", "adverb", "adverbs_mimetic", "lưu loát", ["trôi chảy", "như gió"], "日本語がぺらぺら", "nói tiếng Nhật lưu loát", "彼は日本語をぺらぺらと話せます。", "Anh ấy có thể bắn tiếng Nhật trôi chảy như gió."),
    DictWord("ぎりぎり", "ぎりぎり", "adverb", "adverbs_mimetic", "sát nút", ["vừa vặn", "suýt soát"], "ぎりぎり間に合う", "kịp sát nút giờ", "電車が出発する直前、ぎりぎりで間に合いました！", "Ngay trước lúc tàu chạy, tôi đã kịp sát nút trong gang tấc!"),
    DictWord("うっかり", "うっかり", "adverb", "adverbs_mimetic", "lỡ đễnh", ["sơ ý", "bất cẩn"], "うっかり忘れる", "lỡ đãng quên bẵng mất", "財布を家にうっかり忘れてしまいました。", "Tôi lỡ đãng để quên ví tiền ở nhà mất rồi."),
    DictWord("ますます", "ますます", "adverb", "adverbs_mimetic", "ngày càng", ["càng ngày càng"], "ますます上達する", "ngày càng tiến bộ", "練習すればするほど、日本語がますます楽しくなります。", "Càng luyện tập nhiều thì học tiếng Nhật lại càng thấy vui."),
    DictWord("ついに", "ついに", "adverb", "adverbs_mimetic", "cuối cùng thì", ["rốt cuộc"], "ついに完成した", "cuối cùng đã hoàn thành", "1年間の努力が実を結び、ついに合格しました！", "Nỗ lực suốt một năm đã đơm hoa kết trái, cuối cùng tôi đã đỗ!"),
    DictWord("すっきり", "すっきり", "adverb", "adverbs_mimetic", "sảng khoái", ["nhẹ nhõm", "gọn gàng"], "気分がすっきりする", "tâm trạng sảng khoái nhẹ nhõm", "お風呂に入って気分がすっきりしました。", "Tắm nước nóng xong tâm trạng tôi thấy vô cùng sảng khoái."),
    DictWord("ばったり", "ばったり", "adverb", "adverbs_mimetic", "tình cờ gặp", ["chạm trán bất ngờ"], "ばったり会う", "tình cờ chạm mặt", "駅前で昔の友達にばったり会いました。", "Tôi tình cờ chạm mặt người bạn cũ ngay trước cửa ga."),
    DictWord("ぴったり", "ぴったり", "adverb", "adverbs_mimetic", "vừa khít", ["hoàn toàn khớp", "chuẩn xác"], "サイズがぴったり", "kích cỡ vừa vặn hoàn hảo", "この靴は私の足のサイズにぴったりです。", "Đôi giày này đi vừa khít chân tôi luôn."),
    DictWord("しっかり", "しっかり", "adverb", "adverbs_mimetic", "vững vàng", ["chắc chắn", "chu đáo"], "しっかり食べる", "ăn uống đầy đủ", "明日も早いから、今夜はしっかり寝てくださいね。", "Mai phải dậy sớm nên tối nay bạn nhớ ngủ thật đẫy giấc nhé."),
    DictWord("どんどん", "どんどん", "adverb", "adverbs_mimetic", "nhanh chóng", ["dồn dập", "liên tục"], "どんどん話す", "nói liên tục tự tin", "間違えてもいいので、どんどん日本語を話しましょう！", "Sai cũng không sao, chúng ta hãy cứ tự tin nói thật nhiều nhé!"),
    DictWord("だんだん", "だんだん", "adverb", "adverbs_mimetic", "dần dần", ["từng chút một"], "だんだん慣れる", "dần dần quen thuộc", "日本での生活にもだんだん慣れてきました。", "Tôi cũng đã dần dần thích nghi với cuộc sống tại Nhật."),
    DictWord("わざわざ", "わざわざ", "adverb", "adverbs_mimetic", "cất công", ["không quản công sức"], "わざわざ来てくれる", "cất công lặn lội đến", "遠いところをわざわざお越しいただきありがとうございます。", "Cảm ơn quý khách đã không quản đường xa cất công đến đây ạ."),
    DictWord("せっかく", "せっかく", "adverb", "adverbs_mimetic", "đã mất công", ["hiếm khi có dịp"], "せっかくの機会", "cơ hội quý giá", "せっかく日本に来たのだから、温泉に行きましょう！", "Đã cất công sang Nhật rồi thì nhất định phải đi tắm Onsen nhé!"),
    DictWord("たまたま", "たまたま", "adverb", "adverbs_mimetic", "ngẫu nhiên", ["tình cờ"], "たまたま見つける", "tình cờ nhìn thấy", "本屋でたまたま面白い本を見つけました。", "Tôi tình cờ tìm thấy một cuốn sách rất hay ở hiệu sách."),
    DictWord("やっぱり", "やっぱり", "adverb", "adverbs_mimetic", "quả nhiên", ["đúng như dự đoán"], "やっぱり美味しい", "quả nhiên là ngon tuyệt", "母が作った料理はやっぱり一番美味しいです。", "Cơm mẹ nấu quả nhiên vẫn là ngon số một trên đời."),
]

# =========================================================================
# 4. WORKPLACE & BUSINESS (Công sở, Thương mại & Hou-Ren-So)
# =========================================================================
WORKPLACE_BIZ: list[DictWord] = [
    DictWord("書類", "しょるい", "noun", "workplace_biz", "tài liệu", ["hồ sơ", "giấy tờ"], "書類を提出する", "nộp hồ sơ tài liệu", "会議の前に書類に目を通しておいてください。", "Trước cuộc họp bạn hãy xem qua tập tài liệu này nhé."),
    DictWord("納期", "のうき", "noun", "workplace_biz", "hạn giao hàng", ["deadline", "thời hạn giao việc"], "納期を守る", "đảm bảo đúng hạn giao", "クオリティを保ちながら納期に間に合わせます。", "Chúng tôi sẽ đảm bảo chất lượng và giao đúng thời hạn ạ."),
    DictWord("担当", "たんとう", "noun", "workplace_biz", "phụ trách", ["người chịu trách nhiệm"], "プロジェクトを担当する", "phụ trách dự án", "この案件は私が担当させていただきます。", "Dự án này sẽ do tôi trực tiếp phụ trách ạ."),
    DictWord("検討", "けんとう", "noun", "workplace_biz", "xem xét", ["cân nhắc", "nghiên cứu"], "前向きに検討する", "tích cực xem xét", "ご提案いただいた件、社内で前向きに検討いたします。", "Về đề xuất của quý công ty, chúng tôi sẽ tích cực bàn bạc nội bộ."),
    DictWord("対応", "たいおう", "noun", "workplace_biz", "xử lý", ["đối ứng", "giải quyết"], "迅速に対応する", "xử lý nhanh chóng", "お客様からのご質問に迅速に対応いたします。", "Chúng tôi sẽ giải đáp nhanh chóng thắc mắc của khách hàng."),
    DictWord("打ち合わせ", "うちあわせ", "noun", "workplace_biz", "cuộc họp trao đổi", ["buổi thảo luận", "họp bàn"], "打ち合わせを行う", "tiến hành cuộc họp trao đổi", "明日の午後2時からクライアントと打ち合わせがあります。", "2 giờ chiều mai tôi có buổi họp trao đổi cùng khách hàng."),
    DictWord("議事録", "ぎじろく", "noun", "workplace_biz", "biên bản cuộc họp", ["bản ghi chép họp"], "議事録を作成する", "soạn biên bản cuộc họp", "本日の会議の議事録をまとめてメールで共有します。", "Tôi sẽ tổng hợp biên bản họp hôm nay và gửi qua email cho mọi người."),
    DictWord("見積もり", "みつもり", "noun", "workplace_biz", "báo giá", ["bản ước tính chi phí"], "見積もりを出す", "lập bản báo giá", "本日中にお見積もり書を作成してお送りいたします。", "Tôi sẽ hoàn thành bản báo giá và gửi cho quý khách trong hôm nay."),
    DictWord("請求書", "せいきゅうしょ", "noun", "workplace_biz", "hóa đơn thanh toán", ["giấy đòi tiền"], "請求書を発行する", "xuất hóa đơn thanh toán", "月末までに請求書をお送りいただけますでしょうか？", "Quý công ty gửi hóa đơn thanh toán trước cuối tháng giúp tôi nhé?"),
    DictWord("契約", "けいやく", "noun", "workplace_biz", "hợp đồng", ["giao kèo", "ký kết"], "契約を結ぶ", "ký kết hợp đồng", "無事に新しい取引先と契約を結ぶことができました。", "Chúng tôi đã thuận lợi ký kết hợp đồng với đối tác mới."),
    DictWord("進捗", "しんちょく", "noun", "workplace_biz", "tiến độ", ["tình hình tiến triển"], "進捗を報告する", "báo cáo tiến độ", "現在の進捗状況についてご報告させていただきます。", "Tôi xin phép được báo cáo về tiến độ công việc hiện tại."),
    DictWord("残業", "ざんぎょう", "noun", "workplace_biz", "làm thêm giờ", ["tăng ca", "OT"], "残業をする", "làm thêm giờ", "今日は納期が近いので1時間だけ残業します。", "Hôm nay sắp đến hạn giao việc nên tôi làm thêm 1 tiếng."),
    DictWord("出張", "しゅっちょう", "noun", "workplace_biz", "đi công tác", ["chuyến công tác"], "出張に行く", "đi công tác xa", "来週の月曜日から3日間、大阪へ出張に行きます。", "Từ thứ Hai tuần sau tôi sẽ đi công tác ở Osaka 3 ngày."),
    DictWord("名刺", "めいし", "noun", "workplace_biz", "danh thiếp", ["card visit"], "名刺を交換する", "trao đổi danh thiếp", "初めまして、名刺を交換させていただけますか？", "Lần đầu gặp mặt, xin phép được trao đổi danh thiếp cùng quý vị ạ?"),
    DictWord("引き継ぎ", "ひきつぎ", "noun", "workplace_biz", "bàn giao công việc", ["chuyển giao nhiệm vụ"], "業務を引き継ぐ", "chuyển giao công việc", "有給休暇を取る前にしっかり引き継ぎをしておきます。", "Trước khi nghỉ phép tôi sẽ bàn giao công việc thật chu đáo."),
]

# =========================================================================
# 5. DAILY LIFE & SERVICE (Sinh hoạt, Mua sắm & Dịch vụ)
# =========================================================================
DAILY_LIFE: list[DictWord] = [
    DictWord("お会計", "おかいけい", "noun", "daily_life", "thanh toán", ["tính tiền", "hóa đơn"], "お会計をお願いする", "gọi tính tiền", "すみません、お会計をお願いします。", "Xin lỗi, làm ơn tính tiền giúp tôi với ạ."),
    DictWord("割引", "わりびき", "noun", "daily_life", "giảm giá", ["chiết khấu", "khuyến mãi"], "割引クーポン", "mã giảm giá khuyến mãi", "このクーポンを使うと20パーセント割引になります。", "Dùng mã giảm giá này bạn sẽ được giảm 20%."),
    DictWord("予約", "よやく", "noun", "daily_life", "đặt chỗ", ["đặt bàn", "booking"], "席を予約する", "đặt trước bàn ăn", "金曜日の夜7時にレストランを予約しました。", "Tôi đã đặt bàn ở nhà hàng lúc 7 giờ tối thứ Sáu."),
    DictWord("領収書", "りょうしゅうしょ", "noun", "daily_life", "hóa đơn đỏ", ["hóa đơn thanh toán", "biên lai"], "領収書をもらう", "xin cấp hóa đơn đỏ", "会社名義で領収書をいただけますでしょうか？", "Cho tôi xin hóa đơn đỏ ghi tên công ty được không ạ?"),
    DictWord("注文", "ちゅうもん", "noun", "daily_life", "gọi món", ["đặt hàng", "order"], "注文を取る", "nhận order gọi món", "ご注文が決まりましたらお呼びください。", "Khi nào quý khách chọn xong món xin hãy gọi tôi nhé ạ."),
    DictWord("営業時間", "えいぎょうじかん", "noun", "daily_life", "giờ mở cửa", ["thời gian làm việc"], "営業時間を調べる", "tra cứu giờ mở cửa", "このカフェの営業時間は夜10時までです。", "Quán cà phê này mở cửa phục vụ đến 10 giờ tối."),
    DictWord("定休日", "ていきゅうび", "noun", "daily_life", "ngày nghỉ định kỳ", ["ngày đóng cửa"], "毎週月曜日が定休日", "nghỉ cố định vào thứ Hai", "あのお店は水曜日が定休日なので気をつけてね。", "Quán đó đóng cửa cố định vào thứ Tư nên bạn lưu ý nhé."),
    DictWord("在庫", "ざいこ", "noun", "daily_life", "hàng tồn kho", ["hàng có sẵn"], "在庫を確認する", "kiểm tra hàng trong kho", "あいにくこちらの商品の在庫は切れております。", "Rất tiếc sản phẩm mẫu này hiện tại trong kho đã hết hàng ạ."),
    DictWord("禁煙席", "きんえんせき", "noun", "daily_life", "ghế không hút thuốc", ["khu vực cấm thuốc"], "禁煙席を希望する", "chọn bàn không hút thuốc", "2名ですが、禁煙席は空いていますでしょうか？", "Chúng tôi đi 2 người, bàn khu vực không hút thuốc còn trống không ạ?"),
    DictWord("試着", "しちゃく", "noun", "daily_life", "mặc thử đồ", ["thử quần áo"], "試着室に入る", "vào phòng thử đồ", "この服を着てみたいのですが、試着してもいいですか？", "Tôi muốn mặc thử chiếc áo này xem có vừa không được chứ ạ?"),
    DictWord("配送料", "はいそうりょう", "noun", "daily_life", "phí vận chuyển", ["tiền ship", "cước gửi"], "配送料が無料", "miễn phí vận chuyển", "5,000円以上のお買い上げで配送料が無料になります。", "Đơn hàng trên 5.000 Yên sẽ được miễn phí vận chuyển."),
    DictWord("返品", "へんぴん", "noun", "daily_life", "đổi trả hàng", ["trả lại đồ đã mua"], "商品を返品する", "đổi trả sản phẩm", "レシートがあれば1週間以内なら返品可能です。", "Nếu còn giữ hóa đơn mua hàng thì có thể đổi trả trong vòng 1 tuần."),
    DictWord("終電", "しゅうでん", "noun", "daily_life", "chuyến tàu cuối", ["chuyến xe chót"], "終電を逃す", "lỡ chuyến tàu cuối cùng", "終電に乗り遅れないように急いで駅に向かいました。", "Để không bị lỡ chuyến tàu cuối tôi đã vội vàng chạy ra ga."),
    DictWord("忘れ物", "わすれもの", "noun", "daily_life", "đồ bỏ quên", ["vật đánh rơi"], "忘れ物を届ける", "giao đồ bỏ quên cho quầy", "電車の中に傘を忘れ物をしてしまいました。", "Tôi lỡ bỏ quên cây dù ở trên tàu điện mất rồi."),
    DictWord("両替", "りょうがえ", "noun", "daily_life", "đổi tiền", ["đổi ngoại tệ", "đổi tiền lẻ"], "外貨を両替する", "đổi ngoại tệ", "空港の両替所で日本円をベトナムドンに両替しました。", "Tôi đã đổi tiền Yên sang Đồng Việt Nam tại quầy đổi tiền ở sân bay."),
]

# Combined Pool of All Words
ALL_VOCAB_WORDS: list[DictWord] = (
    ACTION_VERBS + EMOTIONS_ADJ + ADVERBS_MIMETIC + WORKPLACE_BIZ + DAILY_LIFE
)

# Category Map
VOCAB_CATEGORY_MAP: dict[str, list[DictWord]] = {
    "action_verbs": ACTION_VERBS,
    "emotions_adj": EMOTIONS_ADJ,
    "adverbs_mimetic": ADVERBS_MIMETIC,
    "workplace_biz": WORKPLACE_BIZ,
    "daily_life": DAILY_LIFE,
}


def get_all_vocab_words() -> list[DictWord]:
    return ALL_VOCAB_WORDS


def get_easy_vocab() -> list[DictWord]:
    return ALL_VOCAB_WORDS


def get_normal_vocab() -> list[DictWord]:
    return ALL_VOCAB_WORDS


def get_hard_vocab() -> list[DictWord]:
    return ALL_VOCAB_WORDS


EASY_VOCAB = ALL_VOCAB_WORDS
NORMAL_VOCAB = ALL_VOCAB_WORDS
HARD_VOCAB = ALL_VOCAB_WORDS


def get_vocab_by_category(category: str) -> list[DictWord]:
    if not category or category == "all":
        return ALL_VOCAB_WORDS
    return VOCAB_CATEGORY_MAP.get(category, ALL_VOCAB_WORDS)


def search_vocab(query: str) -> list[DictWord]:
    if not query.strip():
        return ALL_VOCAB_WORDS
    q = query.lower().strip()
    return [
        w for w in ALL_VOCAB_WORDS
        if q in w.word.lower()
        or q in w.reading.lower()
        or q in w.meaning_vi.lower()
        or any(q in syn.lower() for syn in w.synonyms_vi)
        or q in w.collocation_ja.lower()
        or q in w.collocation_vi.lower()
        or q in w.example_ja.lower()
        or q in w.example_vi.lower()
    ]
