import re
import unicodedata
from app.domains.learner_memory.contracts import MemoryType


class MemoryKeyResolver:
    """Resolves linguistic correction signals, grammar points, and speaking habits into canonical stable keys."""

    # Pre-mapped canonical grammar/particle patterns
    CANONICAL_PATTERNS: dict[str, tuple[MemoryType, str, str]] = {
        # Particle confusions
        "ha_vs_ga": (MemoryType.PARTICLE, "particle.ha_vs_ga", "Nhầm lẫn giữa trợ từ は và が"),
        "ni_vs_de": (MemoryType.PARTICLE, "particle.ni_vs_de", "Nhầm lẫn giữa trợ từ に và で"),
        "wo_vs_ga": (MemoryType.PARTICLE, "particle.wo_vs_ga", "Nhầm lẫn giữa trợ từ を và が (với thể khả năng/thích)"),
        "to_vs_ya": (MemoryType.PARTICLE, "particle.to_vs_ya", "Nhầm lẫn giữa liệt kê hoàn toàn と và liệt kê tiêu biểu や"),
        "e_vs_ni": (MemoryType.PARTICLE, "particle.e_vs_ni", "Nhầm lẫn hướng chuyển động へ và điểm đến に"),

        # Common Grammar Points
        "wake_de_wa_nai": (MemoryType.GRAMMAR, "grammar.wake_de_wa_nai", "Cấu trúc phủ định một phần 〜わけではない"),
        "te_shimau": (MemoryType.GRAMMAR, "grammar.te_shimau", "Cấu trúc lỡ/hoàn thành 〜てしまう / 〜ちゃう"),
        "te_oku": (MemoryType.GRAMMAR, "grammar.te_oku", "Cấu trúc chuẩn bị trước 〜ておく / 〜とく"),
        "te_miru": (MemoryType.GRAMMAR, "grammar.te_miru", "Cấu trúc thử làm 〜てみる"),
        "to_omou": (MemoryType.GRAMMAR, "grammar.to_omou", "Thể thông thường trước cấu trúc と思う"),
        "koto_ga_aru": (MemoryType.GRAMMAR, "grammar.koto_ga_aru", "Cấu trúc kinh nghiệm đã từng 〜たことがある"),
        "hou_ga_ii": (MemoryType.GRAMMAR, "grammar.hou_ga_ii", "Cấu trúc khuyên bảo 〜たほうがいい"),
        "nakereba_naranai": (MemoryType.GRAMMAR, "grammar.nakereba_naranai", "Cấu trúc phải làm 〜なければならない / なきゃ"),
        "sou_da": (MemoryType.GRAMMAR, "grammar.sou_da", "Phân biệt nghe nói 〜そうだ và dường như 〜そう"),
        "you_da": (MemoryType.GRAMMAR, "grammar.you_da", "Cấu trúc phỏng đoán 〜ようだ / 〜みたい"),

        # Conjugation
        "te_form": (MemoryType.CONJUGATION, "conjugation.te_form", "Chia thể 〜て (âm Te-form)"),
        "nai_form": (MemoryType.CONJUGATION, "conjugation.nai_form", "Chia thể phủ định 〜ない"),
        "ta_form": (MemoryType.CONJUGATION, "conjugation.ta_form", "Chia thể quá khứ 〜た"),
        "potential_form": (MemoryType.CONJUGATION, "conjugation.potential_form", "Chia thể khả năng (Potential form)"),
        "passive_causative": (MemoryType.CONJUGATION, "conjugation.passive_causative", "Chia thể bị động và sai khiến"),
        "i_na_adjective": (MemoryType.CONJUGATION, "conjugation.adjective_inflection", "Biến đổi đuôi tính từ đuôi い và đuôi な"),

        # Politeness & Keigo
        "keigo_avoidance": (MemoryType.POLITENESS, "politeness.keigo_avoidance", "Xu hướng né tránh kính ngữ/khiêm nhường ngữ"),
        "desu_masu_mix": (MemoryType.POLITENESS, "politeness.desu_masu_mix", "Trộn lẫn thể lịch sự (です/ます) và thể ngắn trong cùng đoạn hội thoại"),
        "sonkeigo_kenjougo": (MemoryType.POLITENESS, "politeness.sonkeigo_kenjougo", "Nhầm lẫn giữa Tôn kính ngữ và Khiêm nhường ngữ"),

        # Fillers & Habits
        "excessive_nanka": (MemoryType.FILLER, "filler.excessive_nanka", "Thói quen lạm dụng từ đệm 'なんか'"),
        "excessive_eto": (MemoryType.FILLER, "filler.excessive_eto", "Thói quen ngập ngừng lạm dụng 'ええと / あのー'"),
        "vietnamese_syntax": (MemoryType.SPEAKING_HABIT, "speaking_habit.literal_vietnamese_structure", "Xu hướng dịch nguyên văn cấu trúc câu tiếng Việt sang tiếng Nhật"),
        "short_response": (MemoryType.SPEAKING_HABIT, "speaking_habit.short_unelaborated_answers", "Xu hướng chỉ trả lời quá ngắn, chưa mở rộng ý"),

        # Strengths
        "prompt_turn_continuity": (MemoryType.STRENGTH, "strength.turn_continuity", "Duy trì mạch hội thoại tốt, phản hồi nhanh"),
        "natural_fillers": (MemoryType.STRENGTH, "strength.natural_fillers", "Sử dụng từ đệm (あいづち) tự nhiên"),
        "rich_casual_vocab": (MemoryType.STRENGTH, "strength.rich_casual_vocab", "Vốn từ vựng giao tiếp đời sống phong phú"),
        "good_followup_questions": (MemoryType.STRENGTH, "strength.good_followup_questions", "Chủ động đặt câu hỏi nối tiếp tự nhiên"),
    }

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Normalizes unicode and strips extraneous symbols."""
        if not text:
            return ""
        norm = unicodedata.normalize("NFKC", text.strip().lower())
        return re.sub(r"[\s\-_・/〜~,，.。]+", "_", norm).strip("_")

    @classmethod
    def resolve_key(
        cls,
        category: str,
        identifier_hint: str,
        original_snippet: str | None = None,
    ) -> tuple[MemoryType, str, str]:
        """
        Resolves input signals to a (MemoryType, canonical_key, default_statement) tuple.
        """
        hint_clean = cls.normalize_text(identifier_hint)
        orig_clean = cls.normalize_text(original_snippet or "")
        cat_clean = category.strip().lower()

        # Check explicit particle combinations
        if "は" in identifier_hint and "が" in identifier_hint or "ha_vs_ga" in hint_clean or "は_が" in hint_clean:
            return cls.CANONICAL_PATTERNS["ha_vs_ga"]
        if "に" in identifier_hint and "で" in identifier_hint or "ni_vs_de" in hint_clean:
            return cls.CANONICAL_PATTERNS["ni_vs_de"]
        if "を" in identifier_hint and "が" in identifier_hint or "wo_vs_ga" in hint_clean:
            return cls.CANONICAL_PATTERNS["wo_vs_ga"]

        # Check Japanese grammar substring patterns
        if "わけではない" in identifier_hint or "わけじゃない" in identifier_hint or "wake_de_wa_nai" in hint_clean:
            return cls.CANONICAL_PATTERNS["wake_de_wa_nai"]
        if "てしまう" in identifier_hint or "ちゃう" in identifier_hint or "te_shimau" in hint_clean:
            return cls.CANONICAL_PATTERNS["te_shimau"]
        if "ておく" in identifier_hint or "とく" in identifier_hint or "te_oku" in hint_clean:
            return cls.CANONICAL_PATTERNS["te_oku"]
        if "てみる" in identifier_hint or "te_miru" in hint_clean:
            return cls.CANONICAL_PATTERNS["te_miru"]
        if "と思う" in identifier_hint or "to_omou" in hint_clean:
            return cls.CANONICAL_PATTERNS["to_omou"]
        if "ことがある" in identifier_hint or "koto_ga_aru" in hint_clean:
            return cls.CANONICAL_PATTERNS["koto_ga_aru"]
        if "ほうがいい" in identifier_hint or "hou_ga_ii" in hint_clean:
            return cls.CANONICAL_PATTERNS["hou_ga_ii"]
        if "なければならない" in identifier_hint or "なきゃ" in identifier_hint or "nakereba_naranai" in hint_clean:
            return cls.CANONICAL_PATTERNS["nakereba_naranai"]
        if "そうだ" in identifier_hint or "sou_da" in hint_clean:
            return cls.CANONICAL_PATTERNS["sou_da"]
        if "ようだ" in identifier_hint or "みたい" in identifier_hint or "you_da" in hint_clean:
            return cls.CANONICAL_PATTERNS["you_da"]

        # Check keyword aliases in known patterns
        for pat_key, (m_type, canonical_key, stmt) in cls.CANONICAL_PATTERNS.items():
            if pat_key in hint_clean or pat_key in orig_clean:
                return m_type, canonical_key, stmt

        # Check fillers
        if "なんか" in identifier_hint or "nanka" in hint_clean:
            return cls.CANONICAL_PATTERNS["excessive_nanka"]
        if "ええと" in identifier_hint or "あの" in identifier_hint or "eto" in hint_clean:
            return cls.CANONICAL_PATTERNS["excessive_eto"]

        # Category based fallbacks
        if cat_clean in ("particle", "particles"):
            resolved_key = f"particle.{hint_clean[:40] or 'usage'}"
            return MemoryType.PARTICLE, resolved_key, f"Cách dùng trợ từ ({identifier_hint})"

        if cat_clean in ("conjugation", "inflection"):
            resolved_key = f"conjugation.{hint_clean[:40] or 'verb_form'}"
            return MemoryType.CONJUGATION, resolved_key, f"Chia thể ({identifier_hint})"

        if cat_clean in ("politeness", "keigo", "formality"):
            resolved_key = f"politeness.{hint_clean[:40] or 'formality'}"
            return MemoryType.POLITENESS, resolved_key, f"Độ lịch sự và kính ngữ ({identifier_hint})"

        if cat_clean in ("filler", "fillers"):
            resolved_key = f"filler.{hint_clean[:40] or 'habit'}"
            return MemoryType.FILLER, resolved_key, f"Thói quen dùng từ đệm ({identifier_hint})"

        if cat_clean in ("vocabulary", "word_choice"):
            resolved_key = f"vocab.{hint_clean[:40] or 'usage'}"
            return MemoryType.VOCABULARY, resolved_key, f"Sử dụng từ vựng ({identifier_hint})"

        if cat_clean in ("strength", "positive"):
            resolved_key = f"strength.{hint_clean[:40] or 'speaking'}"
            return MemoryType.STRENGTH, resolved_key, f"Điểm mạnh: {identifier_hint}"

        if cat_clean in ("goal", "learning_goal"):
            resolved_key = f"goal.{hint_clean[:40] or 'target'}"
            return MemoryType.GOAL, resolved_key, f"Mục tiêu: {identifier_hint}"

        # Default to grammar or naturalness
        if "natural" in cat_clean:
            resolved_key = f"naturalness.{hint_clean[:40] or 'expression'}"
            return MemoryType.NATURALNESS, resolved_key, f"Độ tự nhiên ({identifier_hint})"

        resolved_key = f"grammar.{hint_clean[:40] or 'general'}"
        return MemoryType.GRAMMAR, resolved_key, f"Ngữ pháp ({identifier_hint})"
