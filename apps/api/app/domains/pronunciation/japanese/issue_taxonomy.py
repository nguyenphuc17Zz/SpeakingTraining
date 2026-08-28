from enum import Enum


class JapaneseIssueType(str, Enum):
    # Mora & Timing issues
    LONG_VOWEL = "pronunciation.long_vowel"
    SHORT_VOWEL = "pronunciation.short_vowel"
    SMALL_TSU = "pronunciation.small_tsu"         # Gemination / 促音 っ
    N_SOUND = "pronunciation.n_sound"             # 撥音 ん
    YOON = "pronunciation.yoon"                   # 拗音 (きゃ, きゅ, きょ)
    MORA_TIMING = "pronunciation.mora_timing"     # General mora duration balance

    # Phoneme & Articulation issues
    PHONEME_R = "pronunciation.phoneme.r"         # ら・り・る・れ・ろ (avoiding English L/R)
    PHONEME_FU = "pronunciation.phoneme.fu"       # ふ (bilabial fricative vs English F)
    PHONEME_TSU = "pronunciation.phoneme.tsu"     # つ (dental affricate)
    PHONEME_SHI_CHI = "pronunciation.phoneme.shi_chi"  # し vs ち
    PHONEME_ZA_JI = "pronunciation.phoneme.za_ji" # ざ vs じ / ず
    VOICING_ERROR = "pronunciation.voicing"       # 清音 vs 濁音
    DEVOICING_ERROR = "pronunciation.devoicing"   # 無声化 (e.g. です -> desu vs des)

    # Pitch & Prosody issues
    PITCH_HEIBAN = "pitch_accent.heiban"          # 0型
    PITCH_ATAMADAKA = "pitch_accent.atamadaka"    # 1型
    PITCH_NAKADAKA = "pitch_accent.nakadaka"      # 2型+
    PITCH_ODAKA = "pitch_accent.odaka"            # 尾高型
    PITCH_GENERAL = "pitch_accent.general"

    # Rhythm & Intonation
    RHYTHM_RUSH = "rhythm.rushed_mora"
    RHYTHM_DRAG = "rhythm.dragged_pause"
    INTONATION_QUESTION = "intonation.question_rise"
    INTONATION_STATEMENT = "intonation.statement_fall"
    FILLER_HABIT = "fluency.filler_habit"


TAXONOMY_EXPLANATIONS: dict[JapaneseIssueType, dict[str, str]] = {
    JapaneseIssueType.LONG_VOWEL: {
        "title": "Trường âm (Long Vowel)",
        "explanation": "Trường âm tiếng Nhật cần kéo dài đúng 2 mora (2 nhịp đập). Bạn có xu hướng phát âm quá ngắn hoặc ngắt sớm.",
        "practice_tip": "Hãy đếm 2 nhịp vỗ tay đều nhau: nhịp 1 cho nguyên âm gốc, nhịp 2 giữ nguyên khẩu hình âm đó (ví dụ: お・ば・あ・さ・ん = 5 nhịp).",
    },
    JapaneseIssueType.SMALL_TSU: {
        "title": "Âm ngắt (Sokuon / っ)",
        "explanation": "Âm ngắt「っ」chiếm trọn 1 mora tĩnh lặng trước phụ âm tiếp theo. Tránh đọc liền hoặc bỏ quên khoảng dừng.",
        "practice_tip": "Khóa luồng khí ở vòm họng đúng 1 nhịp trống trước khi bật âm tiếp theo (ví dụ: がっ・こう).",
    },
    JapaneseIssueType.N_SOUND: {
        "title": "Âm mũi (Hatsuon / ん)",
        "explanation": "Âm「ん」chiếm 1 mora hoàn chỉnh, khẩu hình thay đổi tùy theo âm đứng sau nó (m, n, ng).",
        "practice_tip": "Đừng nuốt âm「ん」, hãy ngân đủ độ dài 1 nhịp chuẩn (ví dụ: し・ん・ぶ・ん = 4 mora).",
    },
    JapaneseIssueType.YOON: {
        "title": "Ảo âm (Yōon / ゃ・ゅ・ょ)",
        "explanation": "Âm ghép (きゃ, しゃ, ちょ...) kết hợp thành 1 mora duy nhất, không tách làm 2 âm riêng biệt.",
        "practice_tip": "Phát âm dứt khoát trong 1 nhịp đập duy nhất thay vì đọc kéo dài như 'ki-ya'.",
    },
    JapaneseIssueType.PHONEME_R: {
        "title": "Hàng âm R (ら・り・る・れ・ろ)",
        "explanation": "Âm 'R' tiếng Nhật là âm vỗ chân răng (Flap / Tap), khác hoàn toàn âm 'R' cuộn lưỡi tiếng Anh hay 'L'.",
        "practice_tip": "Chạm nhẹ đầu lưỡi vào phần lợi ngay sau răng cửa trên rồi bật nhanh xuống.",
    },
    JapaneseIssueType.PHONEME_FU: {
        "title": "Âm 'Fu' (ふ)",
        "explanation": "Âm 'fu' tiếng Nhật tạo ra bằng hai môi khép nhẹ (không dùng răng cắn môi dưới như âm F tiếng Anh).",
        "practice_tip": "Để hai môi mở tự nhiên và thở nhẹ luồng khí ra ngoài như thổi nến.",
    },
    JapaneseIssueType.PHONEME_TSU: {
        "title": "Âm 'Tsu' (つ)",
        "explanation": "Âm 'tsu' là phụ âm tắc xát (ts), cần phân biệt rõ với âm 'su' (す) hay 'tu'.",
        "practice_tip": "Khép chặt răng, đặt đầu lưỡi sau răng cửa trên rồi thả ra với luồng khí xát mạnh.",
    },
    JapaneseIssueType.PITCH_HEIBAN: {
        "title": "Cao độ Heiban (平板型 - ⓪)",
        "explanation": "Từ loại Heiban bắt đầu thấp ở mora 1, sau đó lên cao ở mora 2 và giữ nguyên cao độ sang trợ từ đứng sau.",
        "practice_tip": "Duy trì cao độ phẳng sau mora đầu tiên, không hạ giọng ở cuối từ (L-H-H-H...).",
    },
    JapaneseIssueType.PITCH_ATAMADAKA: {
        "title": "Cao độ Atamadaka (頭高型 - ①)",
        "explanation": "Từ loại Atamadaka có trọng âm cao ngay ở mora 1, và lập tức hạ thấp xuống ở tất cả các mora còn lại.",
        "practice_tip": "Bắt đầu với âm sắc cao và rõ ở mora 1, sau đó hạ ngay độ cao cho các âm tiếp theo (H-L-L...).",
    },
    JapaneseIssueType.PITCH_NAKADAKA: {
        "title": "Cao độ Nakadaka (中高型)",
        "explanation": "Cao độ bắt đầu thấp, đi lên ở giữa từ và hạ xuống trước khi kết thúc từ.",
        "practice_tip": "Lên giọng ở mora trọng tâm rồi rơi xuống rõ ràng ở các mora phía sau.",
    },
    JapaneseIssueType.PITCH_ODAKA: {
        "title": "Cao độ Odaka (尾高型)",
        "explanation": "Cao độ thấp ở mora 1, cao liên tục đến hết từ, nhưng hạ xuống ngay khi sang trợ từ.",
        "practice_tip": "Giữ âm cao cho đến cuối từ, và hạ giọng khi phát âm trợ từ nối theo.",
    },
    JapaneseIssueType.MORA_TIMING: {
        "title": "Nhịp điệu Mora (Isochrony)",
        "explanation": "Tiếng Nhật là ngôn ngữ có tính đẳng thời theo mora (mỗi mora có thời lượng tương đương nhau).",
        "practice_tip": "Giữ tốc độ đều đặn như nhịp máy đếm nhịp (metronome), tránh dồn dập vào âm nhấn như tiếng Anh/tiếng Việt.",
    },
    JapaneseIssueType.INTONATION_QUESTION: {
        "title": "Ngữ điệu câu hỏi (Rising Intonation)",
        "explanation": "Cuối câu nghi vấn tiếng Nhật cần có cao độ vút lên nhẹ nhàng và tự nhiên.",
        "practice_tip": "Nâng nhẹ pitch ở âm cuối cùng của câu hỏi (か/の...).",
    },
    JapaneseIssueType.INTONATION_STATEMENT: {
        "title": "Ngữ điệu câu trần thuật (Falling Intonation)",
        "explanation": "Cuối câu khẳng định thông thường cần hạ dần cao độ để tạo cảm giác trọn vẹn và tự nhiên.",
        "practice_tip": "Hạ dần tone giọng ở các âm cuối câu (です/ます).",
    },
}
