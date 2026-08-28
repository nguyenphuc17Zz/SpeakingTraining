from typing import Any

from app.domains.learning.contracts import ExerciseType, LearningItemType


EXERCISE_TEMPLATES: dict[str, dict[str, Any]] = {
    # 1. Grammar Roleplay Template (v1)
    "roleplay.grammar.v1": {
        "template_key": "roleplay.grammar.v1",
        "exercise_type": ExerciseType.ROLEPLAY.value,
        "item_type_affinity": LearningItemType.GRAMMAR.value,
        "template_version": "v1",
        "title_template": "Đóng vai hội thoại: Ứng dụng cấu trúc {target_title}",
        "objective_template": "Sử dụng tự nhiên cấu trúc {target_title} trong ngữ cảnh giao tiếp phản xạ.",
        "scenario_template": "Bạn và đồng nghiệp/đối tác đang thảo luận về một vấn đề công việc hoặc kế hoạch cuối tuần.",
        "instruction_template": "Hãy đối đáp tự nhiên bằng tiếng Nhật với trợ lý AI và lồng ghép cấu trúc {target_title} ít nhất 1 lần vào câu trả lời phù hợp.",
        "prompt_frame": "Tạo một tình huống hội thoại 2-3 lượt nói, trong đó người học được khuyến khích sử dụng {target_title}.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 8,
    },

    # 2. Particle Rapid Response Template (v1)
    "rapid_response.particle.v1": {
        "template_key": "rapid_response.particle.v1",
        "exercise_type": ExerciseType.RAPID_RESPONSE.value,
        "item_type_affinity": LearningItemType.PARTICLE.value,
        "template_version": "v1",
        "title_template": "Phản xạ nhanh trợ từ: {target_title}",
        "objective_template": "Luyện phản xạ chọn và nói đúng trợ từ {target_title} trong vòng 3 giây.",
        "scenario_template": "Trợ lý AI đưa ra câu hỏi hoặc tình huống ngắn, bạn phải phản xạ ngay lập tức câu hoàn chỉnh với trợ từ chuẩn.",
        "instruction_template": "Nghe câu hỏi và nói to câu trả lời đầy đủ bằng tiếng Nhật, chú ý phân biệt chính xác trợ từ.",
        "prompt_frame": "Tạo 3 câu hỏi ngắn yêu cầu phản xạ ngay câu có trợ từ {target_title}.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 5,
    },

    # 3. Sentence Transformation (Keigo / Conjugation) Template (v1)
    "sentence_transformation.politeness.v1": {
        "template_key": "sentence_transformation.politeness.v1",
        "exercise_type": ExerciseType.SENTENCE_TRANSFORMATION.value,
        "item_type_affinity": LearningItemType.POLITENESS.value,
        "template_version": "v1",
        "title_template": "Chuyển đổi câu: {target_title}",
        "objective_template": "Chuyển đổi câu từ thể thông thường sang kính ngữ/thể lịch sự công sở.",
        "scenario_template": "Bạn đang tập nói chuyện với cấp trên hoặc khách hàng Nhật Bản.",
        "instruction_template": "Nghe câu văn thông thường từ AI và nói lại câu tương đương ở mức độ lịch sự công sở (Keigo/Kenjougo/Sonkeigo).",
        "prompt_frame": "Đưa ra các câu giao tiếp hàng ngày cần chuyển đổi sang kính ngữ thương mại.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 5,
    },

    # 4. Pronunciation Repeat / Pitch Accent Template (v1)
    "pronunciation_repeat.pronunciation.v1": {
        "template_key": "pronunciation_repeat.pronunciation.v1",
        "exercise_type": ExerciseType.PRONUNCIATION_REPEAT.value,
        "item_type_affinity": LearningItemType.PRONUNCIATION.value,
        "template_version": "v1",
        "title_template": "Luyện chuẩn âm vị & phách: {target_title}",
        "objective_template": "Luyện phát âm chuẩn phách trường âm, âm ngắt hoặc trọng âm Tokyo cho {target_title}.",
        "scenario_template": "Luyện lặp lại theo mẫu chuẩn bản xứ với phân tích phách (mora) và đường cao độ.",
        "instruction_template": "Nghe âm thanh mẫu và ghi âm lại giọng nói của bạn, cố gắng giữ đúng nhịp phách đều đặn.",
        "prompt_frame": "Chọn câu/cụm từ mẫu tiêu biểu có chứa hiện tượng ngữ âm {target_title}.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 5,
    },

    # 5. Free Opinion / Spontaneous Expression Template (v1)
    "opinion.naturalness.v1": {
        "template_key": "opinion.naturalness.v1",
        "exercise_type": ExerciseType.OPINION.value,
        "item_type_affinity": LearningItemType.NATURALNESS.value,
        "template_version": "v1",
        "title_template": "Bày tỏ quan điểm tự nhiên: {target_title}",
        "objective_template": "Bày tỏ ý kiến cá nhân mạch lạc, sử dụng các cách diễn đạt tự nhiên như {target_title}.",
        "scenario_template": "Trao đổi cởi mở về chủ đề công việc, sở thích hoặc trải nghiệm sống tại Nhật Bản.",
        "instruction_template": "Trả lời câu hỏi mở của AI trong 3-4 câu, trình bày rõ lý do và cảm nhận cá nhân.",
        "prompt_frame": "Đưa ra chủ đề thảo luận cởi mở tạo cơ hội tự nhiên cho người học dùng {target_title}.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 7,
    },

    # 6. Reflex Conjugation Blitz Template (v1)
    "reflex.conjugation.v1": {
        "template_key": "reflex.conjugation.v1",
        "exercise_type": ExerciseType.REFLEX_CONJUGATION.value,
        "item_type_affinity": LearningItemType.CONJUGATION.value,
        "template_version": "v1",
        "title_template": "瞬発力・活用: {target_title}",
        "objective_template": "Nghe động từ và dạng chia mục tiêu, phản xạ nói ngay dạng chia đúng trong {timer}s. Luyện automaticity.",
        "scenario_template": "AI hiển thị động từ nguyên thể và yêu cầu dạng chia (ví dụ: 書く → 使役受身・過去). Bạn phản xạ nói ngay.",
        "instruction_template": "Nghe/nhìn động từ và mục tiêu chia thể, nói ngay đáp án chính xác trước khi hết giờ. Timer chỉ là công cụ, độ chính xác là ưu tiên.",
        "prompt_frame": "Tạo bài tập chia động từ phản xạ: cho động từ {target_title} và dạng mục tiêu {target_pattern}.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 3,
    },

    # 7. Reflex Speed Q&A Template (v1)
    "reflex.qna.v1": {
        "template_key": "reflex.qna.v1",
        "exercise_type": ExerciseType.REFLEX_QNA.value,
        "item_type_affinity": LearningItemType.FLUENCY.value,
        "template_version": "v1",
        "title_template": "瞬発 Q&A: {target_title}",
        "objective_template": "Nghe câu hỏi tiếng Nhật và phản xạ trả lời tự nhiên, đầy đủ trong {timer}s.",
        "scenario_template": "Tình huống đời thường/công sở: AI hỏi về kế hoạch cuối tuần, sở thích, công việc. Bạn trả lời ngay.",
        "instruction_template": "Nghe câu hỏi, nói ngay câu trả lời tự nhiên bằng tiếng Nhật (1-2 câu, không cần dài nhưng phải đủ ý).",
        "prompt_frame": "Tạo câu hỏi mở tiếng Nhật tự nhiên để học viên luyện phản xạ nói với {target_title}.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 4,
    },

    # 8. Reflex Sentence Transformation Template (v1)
    "reflex.transformation.v1": {
        "template_key": "reflex.transformation.v1",
        "exercise_type": ExerciseType.REFLEX_TRANSFORMATION.value,
        "item_type_affinity": LearningItemType.GRAMMAR.value,
        "template_version": "v1",
        "title_template": "瞬発・文型変換: {target_title}",
        "objective_template": "Nghe câu gốc, chuyển đổi ngay sang dạng yêu cầu (lịch sự/ casual / quá khứ / phủ định...) trong {timer}s.",
        "scenario_template": "Bạn nhận được câu tiếng Nhật và yêu cầu chuyển đổi (ví dụ: 今日は東京に行きます → カジュアルな過去形).",
        "instruction_template": "Nghe câu và yêu cầu chuyển đổi, nói ngay câu đã biến đổi, giữ nguyên ý nghĩa.",
        "prompt_frame": "Tạo bài tập biến đổi câu tiếng Nhật cho {target_title}.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 4,
    },

    # 9. Reflex Contextual Reaction Template (v1)
    "reflex.context.v1": {
        "template_key": "reflex.context.v1",
        "exercise_type": ExerciseType.REFLEX_CONTEXT.value,
        "item_type_affinity": LearningItemType.NATURALNESS.value,
        "template_version": "v1",
        "title_template": "瞬発・状況対応: {target_title}",
        "objective_template": "Nghe tình huống/ lời nói của đối phương, phản xạ đáp lại tự nhiên đúng ý định giao tiếp trong {timer}s.",
        "scenario_template": "Bạn bè/ đồng nghiệp nói một câu tiếng Nhật, bạn cần phản ứng theo ý định cho trước (ví dụ: 'Tell them it isn't that spicy').",
        "instruction_template": "Nghe tình huống, nói ngay phản hồi tiếng Nhật tự nhiên phù hợp ngữ cảnh và mối quan hệ.",
        "prompt_frame": "Tạo tình huống phản xạ giao tiếp tiếng Nhật tự nhiên cho {target_title} với ngữ cảnh cụ thể.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 4,
    },

    # 10-16. Keigo Studio Templates (v1) — 5 sub-modes + 2 cross
    "keigo.sonkeigo.v1": {
        "template_key": "keigo.sonkeigo.v1",
        "exercise_type": ExerciseType.KEIGO_SONKEIGO.value,
        "item_type_affinity": LearningItemType.POLITENESS.value,
        "template_version": "v1",
        "title_template": "敬語・尊敬語: {target_title}",
        "objective_template": "Chuyển câu về thể tôn kính 尊敬語 đúng hướng Uchi/Soto, giữ tự nhiên.",
        "scenario_template": "Bạn nói về hành động của khách hàng/cấp trên (Soto) trước mặt họ.",
        "instruction_template": "Nghe câu thường và nói lại bằng 尊敬語 (ví dụ: 見る → ご覧になる) trước khi hết giờ.",
        "prompt_frame": "Tạo bài tập 尊敬語 cho {target_title} với ngữ cảnh tôn kính người nghe/đối tượng Soto.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 5,
    },
    "keigo.kenjougo.v1": {
        "template_key": "keigo.kenjougo.v1",
        "exercise_type": ExerciseType.KEIGO_KENJOUGO.value,
        "item_type_affinity": LearningItemType.POLITENESS.value,
        "template_version": "v1",
        "title_template": "敬語・謙譲語: {target_title}",
        "objective_template": "Chuyển câu về thể khiêm nhường 謙譲語 đúng hướng Uchi→Soto.",
        "scenario_template": "Bạn nói về hành động của mình/nhóm mình (Uchi) trước khách hàng (Soto).",
        "instruction_template": "Nghe câu thường và nói lại bằng 謙譲語 (ví dụ: 見る → 拝見する) trước khi hết giờ.",
        "prompt_frame": "Tạo bài tập 謙譲語 cho {target_title} với ngữ cảnh khiêm nhường hành động của mình.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 5,
    },
    "keigo.teineigo.v1": {
        "template_key": "keigo.teineigo.v1",
        "exercise_type": ExerciseType.KEIGO_TEINEIGO.value,
        "item_type_affinity": LearningItemType.POLITENESS.value,
        "template_version": "v1",
        "title_template": "丁寧語・美化語: {target_title}",
        "objective_template": "Chuyển câu sang 丁寧体/美化語 tự nhiên, đúng です/ます và お/ご.",
        "scenario_template": "Giao tiếp công sở lịch sự, cần giữ 丁寧語 nhất quán.",
        "instruction_template": "Nghe câu casual và nói lại bằng 丁寧語/美化語 (です/ます, お/ご) trước khi hết giờ.",
        "prompt_frame": "Tạo bài tập 丁寧語 cho {target_title} với ngữ cảnh polite nhất quán.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 4,
    },
    "keigo.transformation.v1": {
        "template_key": "keigo.transformation.v1",
        "exercise_type": ExerciseType.KEIGO_TRANSFORMATION.value,
        "item_type_affinity": LearningItemType.POLITENESS.value,
        "template_version": "v1",
        "title_template": "敬語・文体変換: {target_title}",
        "objective_template": "Chuyển đổi nhanh giữa タメ口↔丁寧体↔ビジネス敬語 theo mục tiêu.",
        "scenario_template": "Bạn nhận câu ở một register và cần chuyển sang register mục tiêu (ví dụ: タメ口→ビジネス敬語).",
        "instruction_template": "Nghe câu gốc và target register, nói ngay câu đã chuyển đổi, giữ ý nghĩa.",
        "prompt_frame": "Tạo bài tập biến đổi register cho {target_title} giữa các mức politeness.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 5,
    },
    "keigo.context.v1": {
        "template_key": "keigo.context.v1",
        "exercise_type": ExerciseType.KEIGO_CONTEXT.value,
        "item_type_affinity": LearningItemType.POLITENESS.value,
        "template_version": "v1",
        "title_template": "敬語・状況判断: {target_title}",
        "objective_template": "Chọn kính ngữ đúng theo Uchi/Soto và quan hệ người nói/người nghe/đối tượng.",
        "scenario_template": "Tình huống công sở: khách hỏi về sếp bên bạn, hoặc bạn hỏi về khách.",
        "instruction_template": "Nghe tình huống, xác định hướng kính ngữ (尊敬/謙譲) và nói câu phù hợp.",
        "prompt_frame": "Tạo tình huống Uchi/Soto cho {target_title} để kiểm tra hướng kính ngữ.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 5,
    },
    "keigo.doctor.v1": {
        "template_key": "keigo.doctor.v1",
        "exercise_type": ExerciseType.KEIGO_DOCTOR.value,
        "item_type_affinity": LearningItemType.POLITENESS.value,
        "template_version": "v1",
        "title_template": "Keigo Doctor: {target_title}",
        "objective_template": "Phát hiện lỗi kính ngữ (二重敬語, hướng sai, Uchi/Soto sai) và sửa.",
        "scenario_template": "Câu sau có lỗi kính ngữ: hãy phát hiện và nói lại câu đúng.",
        "instruction_template": "Nghe câu lỗi, chỉ ra loại lỗi và nói lại câu tự nhiên đúng.",
        "prompt_frame": "Tạo câu lỗi kính ngữ cho {target_title} (double keigo/wrong direction) và đáp án đúng.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 5,
    },
    "keigo.naturalness.v1": {
        "template_key": "keigo.naturalness.v1",
        "exercise_type": ExerciseType.KEIGO_NATURALNESS.value,
        "item_type_affinity": LearningItemType.POLITENESS.value,
        "template_version": "v1",
        "title_template": "自然さ判定: {target_title}",
        "objective_template": "Đánh giá câu có tự nhiên trong ngữ cảnh hay không (NATURAL/SLIGHTLY_AWKWARD/INAPPROPRIATE).",
        "scenario_template": "Câu cho sẵn trong ngữ cảnh cụ thể — bạn đánh giá độ tự nhiên và sửa nếu cần.",
        "instruction_template": "Chọn nhãn tự nhiên và nói lại phiên bản tự nhiên hơn nếu cần.",
        "prompt_frame": "Tạo câu hỏi naturalness cho {target_title} với các mức độ trang trọng khác nhau.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 3,
    },

    # 17-21 Pitch Lab Templates (v1) — 5 sub-modes
    "pitch.minimal_pair.v1": {
        "template_key": "pitch.minimal_pair.v1",
        "exercise_type": ExerciseType.PITCH_MINIMAL_PAIR.value,
        "item_type_affinity": LearningItemType.PITCH_ACCENT.value,
        "template_version": "v1",
        "title_template": "高低ミニマルペア: {target_title}",
        "objective_template": "Nghe và phân biệt cặp từ cùng đọc khác cao độ (ví dụ: 雨/飴).",
        "scenario_template": "Hai từ cùng đọc あめ nhưng cao độ khác nhau — bạn nghe và chọn/nghe và nói.",
        "instruction_template": "Nghe cặp từ, chọn đúng theo nghĩa/câu hỏi, hoặc nói lại với cao độ đúng.",
        "prompt_frame": "Tạo bài tập minimal pair cho {target_title} với cùng reading khác accent pattern.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 4,
    },
    "pitch.mora_length.v1": {
        "template_key": "pitch.mora_length.v1",
        "exercise_type": ExerciseType.PITCH_MORA_LENGTH.value,
        "item_type_affinity": LearningItemType.PITCH_ACCENT.value,
        "template_version": "v1",
        "title_template": "モーラ長: {target_title}",
        "objective_template": "Phân biệt trường âm/促音/撥音 (おじさん↔おじいさん, きて↔きって).",
        "scenario_template": "Cặp từ khác số mora — bạn nghe và nói đúng độ dài.",
        "instruction_template": "Nghe và nói đúng mora, giữ timing đều, không kéo/dừng sai.",
        "prompt_frame": "Tạo bài tập mora length cho {target_title} với khác biệt mora rõ rệt.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 4,
    },
    "pitch.devoicing.v1": {
        "template_key": "pitch.devoicing.v1",
        "exercise_type": ExerciseType.PITCH_VOWEL_DEVOICING.value,
        "item_type_affinity": LearningItemType.PITCH_ACCENT.value,
        "template_version": "v1",
        "title_template": "無声化: {target_title}",
        "objective_template": "Luyện vô thanh hóa nguyên âm (です→des, すき).",
        "scenario_template": "Từ có い/う giữa phụ âm vô thanh — nói tự nhiên, không gượng ép.",
        "instruction_template": "Nghe mẫu, nói lại với mức vô thanh tự nhiên, không bắt buộc 100% silence.",
        "prompt_frame": "Tạo bài tập devoicing cho {target_title} với môi trường âm vị phù hợp.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 4,
    },
    "pitch.contour.v1": {
        "template_key": "pitch.contour.v1",
        "exercise_type": ExerciseType.PITCH_CONTOUR.value,
        "item_type_affinity": LearningItemType.PITCH_ACCENT.value,
        "template_version": "v1",
        "title_template": "ピッチ曲線: {target_title}",
        "objective_template": "Tập đường cao độ theo mora, chú ý downstep timing.",
        "scenario_template": "Xem pattern L H H L + mora boundaries, nói theo, so sánh contour.",
        "instruction_template": "Nói theo mẫu, giữ relative pitch (không so Hz tuyệt đối), chú ý nơi hạ cao độ.",
        "prompt_frame": "Tạo bài tập pitch contour cho {target_title} với expected pattern rõ.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 5,
    },
    "pitch.recognition.v1": {
        "template_key": "pitch.recognition.v1",
        "exercise_type": ExerciseType.PITCH_RECOGNITION.value,
        "item_type_affinity": LearningItemType.PITCH_ACCENT.value,
        "template_version": "v1",
        "title_template": "聞き分け: {target_title}",
        "objective_template": "Nghe A/B và chọn đúng cao độ/từ (không cần nói).",
        "scenario_template": "Nghe hai phát âm cùng từ khác accent, chọn đáp án đúng.",
        "instruction_template": "Nghe và chọn A hoặc B, không cần ghi âm ở bước này.",
        "prompt_frame": "Tạo bài tập nhận biết cao độ cho {target_title} với A/B contrast.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 3,
    },

    # 22-23 Situational Roleplay Templates (v1)
    "situational.roleplay.v1": {
        "template_key": "situational.roleplay.v1",
        "exercise_type": ExerciseType.SITUATIONAL_ROLEPLAY.value,
        "item_type_affinity": LearningItemType.NATURALNESS.value,
        "template_version": "v1",
        "title_template": "場面ロールプレイ: {target_title}",
        "objective_template": "Hoàn thành nhiệm vụ trong tình huống {target_title} với giao tiếp tự nhiên.",
        "scenario_template": "Bạn ở {location} với vai {role} — mục tiêu: {goal}. Có thể có sự kiện bất ngờ.",
        "instruction_template": "Nói tự nhiên bằng tiếng Nhật, xử lý tình huống và hoàn thành mục tiêu.",
        "prompt_frame": "Tạo tình huống roleplay cho {target_title} với location/role/goal đa dạng.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 5,
    },
    "situational.scenario.v1": {
        "template_key": "situational.scenario.v1",
        "exercise_type": ExerciseType.SITUATIONAL_SCENARIO.value,
        "item_type_affinity": LearningItemType.NATURALNESS.value,
        "template_version": "v1",
        "title_template": "シナリオ: {target_title}",
        "objective_template": "Xử lý tình huống {target_title} với sự kiện động và yêu cầu ẩn.",
        "scenario_template": "Tình huống ngẫu nhiên: {location} — {goal} — có thể có thay đổi lịch/bất ngờ.",
        "instruction_template": "Phản hồi linh hoạt, xác nhận thông tin, xử lý sự cố tự nhiên.",
        "prompt_frame": "Tạo scenario cho {target_title} với ràng buộc và sự kiện.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 5,
    },
    # 24 Monologue — 1-Minute Speech (Mode 5)
    "speech.monologue.v1": {
        "template_key": "speech.monologue.v1",
        "exercise_type": ExerciseType.SPEECH_MONOLOGUE.value,
        "item_type_affinity": LearningItemType.FLUENCY.value,
        "template_version": "v1",
        "title_template": "1分間スピーチ: {target_title}",
        "objective_template": "Nói liên tục {target_title} trong thời lượng yêu cầu, giữ coherence và kết luận rõ.",
        "scenario_template": "Bạn có {timer} giây chuẩn bị, sau đó nói liên tục về chủ đề được giao, tuân thủ constraints.",
        "instruction_template": "Chuẩn bị {timer} giây, sau đó nói liên tục bằng tiếng Nhật về {target_title}, đáp ứng constraints, kết thúc có kết luận.",
        "prompt_frame": "Tạo bài tập monologue {target_title} với genre/constraint/duration phù hợp level.",
        "expected_pattern_rules": ["{target_pattern}"],
        "default_estimated_minutes": 2,
    },
}


def get_template_for_type(exercise_type: str, item_type: str | None = None) -> dict[str, Any]:
    """Retrieves best matching exercise template or a robust fallback."""
    # Try exact match
    if item_type:
        key = f"{exercise_type}.{item_type}.v1"
        if key in EXERCISE_TEMPLATES:
            return EXERCISE_TEMPLATES[key]

    # Try any template for this exercise_type
    for k, t in EXERCISE_TEMPLATES.items():
        if t["exercise_type"] == exercise_type:
            return t

    # Default fallback
    return EXERCISE_TEMPLATES["roleplay.grammar.v1"]
