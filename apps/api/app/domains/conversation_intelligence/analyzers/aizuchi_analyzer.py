import re
from typing import Any

from app.domains.conversation_intelligence.contracts import (
    AizuchiCategory,
    AizuchiEvaluation,
    AizuchiRegister,
    AnalysisConfidence,
    CorrectionCategory,
    CorrectionItem,
    CorrectionSeverity,
)


class AizuchiAnalyzer:
    """Evaluates Japanese conversational backchanneling (Aizuchi / 相槌),

    turn-initial reactive prefaces, and clause-boundary SLA dynamics.

    Linguistic Foundations:
    - Maynard (1989): Japanese Conversation (Aizuchi occurs 2-3x more often than in English).
    - Clancy et al. (1996) & Tanaka (1999): Clause-boundary backchannels and epistemic alignment.
    - Ide (1989): Wakimae (discernment) in register appropriateness (formal vs casual).
    """

    # 1. Taxonomies of Standalone Aizuchi
    CONTINUERS_CASUAL = {"うん", "ふん", "うーん"}
    CONTINUERS_POLITE = {"はい"}
    CONTINUERS_FORMAL = {"ええ", "承知いたしました", "かしこまりました"}

    AGREEMENT_CASUAL = {"だよね", "そうそう", "ほんとそれ", "それな", "確かに", "その通り"}
    AGREEMENT_POLITE = {"そうですね", "その通りです", "確かにそうですね", "そう思います"}
    AGREEMENT_FORMAL = {"おっしゃる通りです", "ごもっともです", "おっしゃる通りでございます"}

    RESONANCE_CASUAL = {"まじで", "へえ", "すごい", "うそ", "嘘でしょ", "やばい", "大変だったね"}
    RESONANCE_POLITE = {"本当ですか", "すごいですね", "それは大変でしたね", "素晴らしいですね", "驚きました"}
    RESONANCE_FORMAL = {"誠に恐れ入ります", "お気の毒でございます", "大変光栄に存じます"}

    UNDERSTANDING_CASUAL = {"わかった", "了解"}
    UNDERSTANDING_POLITE = {"分かりました", "了解しました", "承知しました", "なるほど"}
    UNDERSTANDING_FORMAL = {"理解いたしました", "承知いたしました", "かしこまりました"}

    # Turn-Initial Reactive Preface Patterns
    PREFACE_PATTERNS = [
        (re.compile(r"^(そうですね[、。,\.\s]?|そうです[、。,\.\s]?)", re.UNICODE), "そうですね", AizuchiCategory.AGREEMENT, AizuchiRegister.POLITE),
        (re.compile(r"^(おっしゃる通り(です|でございます)?[、。,\.\s]?)", re.UNICODE), "おっしゃる通りです", AizuchiCategory.AGREEMENT, AizuchiRegister.FORMAL),
        (re.compile(r"^(確かに(そうですね)?[、。,\.\s]?)", re.UNICODE), "確かに", AizuchiCategory.AGREEMENT, AizuchiRegister.POLITE),
        (re.compile(r"^(その通り(です)?[、。,\.\s]?)", re.UNICODE), "その通りです", AizuchiCategory.AGREEMENT, AizuchiRegister.POLITE),
        (re.compile(r"^(だよね[、。,\.\s]?|そうそう[、。,\.\s]?)", re.UNICODE), "だよね", AizuchiCategory.AGREEMENT, AizuchiRegister.CASUAL),
        (re.compile(r"^(ええ[、。,\.\s]?)", re.UNICODE), "ええ", AizuchiCategory.CONTINUER, AizuchiRegister.FORMAL),
        (re.compile(r"^(はい[、。,\.\s]?)", re.UNICODE), "はい", AizuchiCategory.CONTINUER, AizuchiRegister.POLITE),
        (re.compile(r"^(うん[、。,\.\s]?)", re.UNICODE), "うん", AizuchiCategory.CONTINUER, AizuchiRegister.CASUAL),
        (re.compile(r"^(なるほど(ですね)?[、。,\.\s]?)", re.UNICODE), "なるほど", AizuchiCategory.UNDERSTANDING, AizuchiRegister.POLITE),
        (re.compile(r"^(本当ですか[、。,\.\s]?|まじで[、。,\.\s]?)", re.UNICODE), "本当ですか", AizuchiCategory.EMOTIONAL_RESONANCE, AizuchiRegister.POLITE),
    ]

    # Preceding Clause Boundary Reactive Triggers (Tanaka 1999)
    CLAUSE_BOUNDARY_TRIGGERS = [
        "ね", "よね", "よ", "かな", "かしら", "けど", "けれど", "が", "から", "ので", "たら", "ば", "と", "し", "て", "で", "ですか", "でしょうか"
    ]

    @classmethod
    def is_standalone_aizuchi(cls, text: str) -> bool:
        """Determines if the utterance consists purely of an Aizuchi backchannel."""
        clean = text.strip().rstrip("。、！？!? ")
        all_tokens = (
            cls.CONTINUERS_CASUAL | cls.CONTINUERS_POLITE | cls.CONTINUERS_FORMAL
            | cls.AGREEMENT_CASUAL | cls.AGREEMENT_POLITE | cls.AGREEMENT_FORMAL
            | cls.RESONANCE_CASUAL | cls.RESONANCE_POLITE | cls.RESONANCE_FORMAL
            | cls.UNDERSTANDING_CASUAL | cls.UNDERSTANDING_POLITE | cls.UNDERSTANDING_FORMAL
            | {"こんにちは", "ありがとう", "どうも", "なるほどですね"}
        )
        return clean in all_tokens

    @classmethod
    def classify_token(cls, token: str) -> tuple[AizuchiCategory, AizuchiRegister]:
        """Maps a backchannel token to its SLA category and register."""
        clean = token.strip().rstrip("。、！？!? ")
        if clean in cls.CONTINUERS_CASUAL:
            return AizuchiCategory.CONTINUER, AizuchiRegister.CASUAL
        if clean in cls.CONTINUERS_POLITE:
            return AizuchiCategory.CONTINUER, AizuchiRegister.POLITE
        if clean in cls.CONTINUERS_FORMAL:
            return AizuchiCategory.CONTINUER, AizuchiRegister.FORMAL

        if clean in cls.AGREEMENT_CASUAL:
            return AizuchiCategory.AGREEMENT, AizuchiRegister.CASUAL
        if clean in cls.AGREEMENT_POLITE:
            return AizuchiCategory.AGREEMENT, AizuchiRegister.POLITE
        if clean in cls.AGREEMENT_FORMAL:
            return AizuchiCategory.AGREEMENT, AizuchiRegister.FORMAL

        if clean in cls.RESONANCE_CASUAL:
            return AizuchiCategory.EMOTIONAL_RESONANCE, AizuchiRegister.CASUAL
        if clean in cls.RESONANCE_POLITE:
            return AizuchiCategory.EMOTIONAL_RESONANCE, AizuchiRegister.POLITE
        if clean in cls.RESONANCE_FORMAL:
            return AizuchiCategory.EMOTIONAL_RESONANCE, AizuchiRegister.FORMAL

        if clean in cls.UNDERSTANDING_CASUAL:
            return AizuchiCategory.UNDERSTANDING, AizuchiRegister.CASUAL
        if clean in cls.UNDERSTANDING_POLITE or clean == "なるほどですね":
            return AizuchiCategory.UNDERSTANDING, AizuchiRegister.POLITE
        if clean in cls.UNDERSTANDING_FORMAL:
            return AizuchiCategory.UNDERSTANDING, AizuchiRegister.FORMAL

        return AizuchiCategory.NONE, AizuchiRegister.NEUTRAL

    @classmethod
    def detect_clause_boundary_match(cls, previous_turns: list[dict[str, Any]]) -> bool:
        """Detects whether the partner's preceding turn ended with an SLA clause-boundary trigger."""
        if not previous_turns:
            return False
        last_turn = previous_turns[-1]
        if last_turn.get("speaker") == "user":
            return False
        text = str(last_turn.get("transcript", "")).strip().rstrip("。、！？!? ")
        return any(text.endswith(trigger) for trigger in cls.CLAUSE_BOUNDARY_TRIGGERS)

    @classmethod
    def evaluate(
        cls,
        user_transcript: str,
        persona_role: str = "Partner",
        previous_turns: list[dict[str, Any]] | None = None,
    ) -> tuple[AizuchiEvaluation, list[CorrectionItem]]:
        """Comprehensive evaluation of conversational backchanneling and turn-taking."""
        clean_text = user_transcript.strip()
        prev_turns = previous_turns or []
        corrections: list[CorrectionItem] = []
        clause_matched = cls.detect_clause_boundary_match(prev_turns)

        role_lower = persona_role.lower()
        is_formal_partner = any(
            r in role_lower for r in ["interviewer", "interview", "boss", "tanaka", "teacher", "sensei", "senior", "formal", "manager"]
        )
        is_casual_partner = any(
            r in role_lower for r in ["friend", "casual", "tameguchi", "peer", "classmate"]
        )

        # Case A: Standalone Aizuchi Utterance
        if cls.is_standalone_aizuchi(clean_text):
            token_clean = clean_text.rstrip("。、！？!? ")
            category, register = cls.classify_token(token_clean)

            # Politeness & Wakimae verification
            if is_formal_partner and register == AizuchiRegister.CASUAL:
                corrected = "はい" if category == AizuchiCategory.CONTINUER else "そうですね"
                corrections.append(
                    CorrectionItem(
                        category=CorrectionCategory.POLITENESS,
                        severity=CorrectionSeverity.MUST_FIX,
                        original=token_clean,
                        corrected=corrected,
                        explanation=f"Khi đối thoại với {persona_role}, sử dụng '{token_clean}' (Tameguchi) là thiếu tôn kính. Hãy dùng '{corrected}' để giữ sự nhã nhặn.",
                        confidence=AnalysisConfidence.HIGH,
                        severity_score=85,
                        context_note="Quy tắc Wakimae: Thể lịch sự bắt buộc với cấp trên/người phỏng vấn.",
                    )
                )
                evaluation = AizuchiEvaluation(
                    detected_token=token_clean,
                    category=category,
                    formality_register=register,
                    is_turn_initial_preface=False,
                    is_register_appropriate=False,
                    clause_boundary_matched=clause_matched,
                    feedback_vi=f"Cảnh báo kính ngữ: Tránh dùng '{token_clean}' khi phỏng vấn hoặc nói chuyện với cấp trên.",
                    naturalness_bonus=0,
                )
                return evaluation, corrections

            if is_formal_partner and token_clean in ("なるほど", "なるほどですね"):
                corrections.append(
                    CorrectionItem(
                        category=CorrectionCategory.POLITENESS,
                        severity=CorrectionSeverity.SHOULD_FIX,
                        original=token_clean,
                        corrected="おっしゃる通りです",
                        explanation="Trong giao tiếp công sở Nhật Bản, 'なるほど' mang sắc thái đánh giá người khác từ vị thế ngang hoặc trên. Với cấp trên/người phỏng vấn, hãy dùng 'おっしゃる通りです' hoặc '承知いたしました'.",
                        confidence=AnalysisConfidence.HIGH,
                        severity_score=60,
                        context_note="Quy tắc Baito Keigo & kính ngữ thương mại.",
                    )
                )
                evaluation = AizuchiEvaluation(
                    detected_token=token_clean,
                    category=AizuchiCategory.UNDERSTANDING,
                    formality_register=AizuchiRegister.POLITE,
                    is_turn_initial_preface=False,
                    is_register_appropriate=False,
                    clause_boundary_matched=clause_matched,
                    feedback_vi="Nên thay 'なるほど' bằng 'おっしゃる通りです' với người phỏng vấn/cấp trên.",
                    naturalness_bonus=0,
                )
                return evaluation, corrections

            if is_casual_partner and register == AizuchiRegister.FORMAL:
                corrections.append(
                    CorrectionItem(
                        category=CorrectionCategory.NATURALNESS,
                        severity=CorrectionSeverity.NATIVE_ALTERNATIVE,
                        original=token_clean,
                        corrected="うん",
                        explanation=f"Với {persona_role} (bạn bè), cách nói '{token_clean}' quá trịnh trọng và tạo khoảng cách. Dùng 'うん' hoặc 'だよね' sẽ thân thiết hơn.",
                        confidence=AnalysisConfidence.MEDIUM,
                        severity_score=30,
                    )
                )

            # Valid Standalone Aizuchi
            bonus = 8 if clause_matched else 5
            category_names_vi = {
                AizuchiCategory.CONTINUER: "Lắng nghe & Khích lệ (促し・傾聴)",
                AizuchiCategory.AGREEMENT: "Tán đồng & Đồng thuận (同意・同調)",
                AizuchiCategory.EMOTIONAL_RESONANCE: "Phản hồi cảm xúc & Đồng cảm (驚き・共感)",
                AizuchiCategory.UNDERSTANDING: "Tiếp nhận thông tin (理解・納得)",
            }
            evaluation = AizuchiEvaluation(
                detected_token=token_clean,
                category=category,
                formality_register=register,
                is_turn_initial_preface=False,
                is_register_appropriate=True,
                clause_boundary_matched=clause_matched,
                feedback_vi=f"Phản hồi 相槌 xuất sắc: {category_names_vi.get(category, 'Tự nhiên')}." + (" Bắt nhịp chuẩn xác điểm kết câu của đối phương!" if clause_matched else ""),
                naturalness_bonus=bonus,
            )
            return evaluation, corrections

        # Case B: Multi-word Turn with Turn-Initial Reactive Preface
        for pattern, _base_token, cat, reg in cls.PREFACE_PATTERNS:
            match = pattern.match(clean_text)
            if match:
                matched_str = match.group(1)
                # Check formal vs casual appropriateness of the preface
                is_appropriate = True
                if is_formal_partner and reg == AizuchiRegister.CASUAL:
                    is_appropriate = False
                    corrections.append(
                        CorrectionItem(
                            category=CorrectionCategory.POLITENESS,
                            severity=CorrectionSeverity.SHOULD_FIX,
                            original=matched_str.strip(),
                            corrected="そうですね、",
                            explanation=f"Tiền tố mở đầu '{matched_str.strip()}' là văn phong thân mật (Tameguchi). Khi nói với {persona_role}, hãy dùng 'そうですね、' để trang trọng hơn.",
                            confidence=AnalysisConfidence.HIGH,
                            severity_score=65,
                        )
                    )

                bonus = 10 if clause_matched else 7
                evaluation = AizuchiEvaluation(
                    detected_token=matched_str.strip(),
                    category=AizuchiCategory.TURN_INITIAL_PREFACE,
                    formality_register=reg,
                    is_turn_initial_preface=True,
                    is_register_appropriate=is_appropriate,
                    clause_boundary_matched=clause_matched,
                    feedback_vi="Mở đầu lượt lời mượt mà (Turn-Initial Preface), tạo cảm giác hội thoại tự nhiên của người bản xứ!",
                    naturalness_bonus=bonus if is_appropriate else 0,
                )
                return evaluation, corrections

        # Case C: Standard turn without Aizuchi preface
        evaluation = AizuchiEvaluation(
            detected_token=None,
            category=AizuchiCategory.NONE,
            formality_register=AizuchiRegister.NEUTRAL,
            is_turn_initial_preface=False,
            is_register_appropriate=True,
            clause_boundary_matched=clause_matched,
            feedback_vi=None,
            naturalness_bonus=0,
        )
        return evaluation, corrections
