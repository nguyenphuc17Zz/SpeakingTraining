"""PragmaticsEngine — Sociolinguistic Politeness Matrix & Business Appropriateness.

Implements:
1. Ide's Wakimae (わきまえ) & Relative Honorifics (相対敬語): In-group humbling rule for business.
2. Brown & Levinson's Sociolinguistic Politeness Theory (W = P + D + R).
3. Baito Keigo (バイト敬語 / マニュアル敬語) detection & correction.
4. Cushion Words (クッション言葉) detection & communicative softness scoring.
"""

from __future__ import annotations

import re
from typing import Any

from app.domains.keigo.social_context import Group, PersonRole, Register, Situation, SocialContext

# Cushion Words (クッション言葉) dictionary categorized by pragmatic function
CUSHION_WORDS: dict[str, list[str]] = {
    "request": [
        "恐れ入りますが",
        "恐縮ですが",
        "お手数をおかけしますが",
        "お手数をおかけいたしますが",
        "差し支えなければ",
        "差し支えございませんでしたら",
        "ご都合がよろしければ",
        "ご面倒をおかけしますが",
        "ご面倒をおかけいたしますが",
        "ご多忙のところ恐縮ですが",
        "お忙しいところ恐縮ですが",
        "ご多用のところ恐れ入りますが",
        "誠に恐縮ではございますが",
    ],
    "refusal": [
        "あいにくですが",
        "あいにくではございますが",
        "誠に心苦しいのですが",
        "誠に心苦しい限りですが",
        "大変申し上げにくいのですが",
        "申し上げにくいのですが",
        "せっかくのお申し出ですが",
        "せっかくではございますが",
        "ご期待に沿えず申し訳ございませんが",
        "ご意向に添えず誠に申し訳ありませんが",
    ],
    "inquiry": [
        "失礼ですが",
        "失礼とは存じますが",
        "お伺いしたいのですが",
        "お尋ねしたいのですが",
        "重ねて恐縮ですが",
        "不躾ながら",
        "念のため確認させていただきたいのですが",
    ],
}

ALL_CUSHION_PHRASES = [phrase for phrases in CUSHION_WORDS.values() for phrase in phrases]

# Baito Keigo (バイト敬語) patterns to detect and correct
BAITO_KEIGO_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    # 1. 〜の方 (ほう) as vague noun filler
    (
        re.compile(r"([^\s。、！？]{2,6}?)の方(が|を|に|で|は|から)"),
        "「〜の方（ほう）」の不適切な用法",
        "方角や比較でない対象に「〜の方」を使うのはバイト敬語です。「{stem}{particle}」と直接表現します",
    ),
    # 2. 〜からお預かりします
    (
        re.compile(r"([^\s。、！？]+?)からお預かり(し|いたし|ます)"),
        "「〜からお預かり」の不自然な用法",
        "お金や書類自体から預かるわけではないため、「{stem}をお預かりいたします」が正確です",
    ),
    # 3. よろしかったでしょうか (pseudo-polite past tense)
    (
        re.compile(r"よろしかった(でしょうか|ですか)"),
        "「よろしかったでしょうか」の不適切な過去形",
        "現在確認している事項に対して過去形を使うのはマニュアル敬語です。「よろしいでしょうか」を用います",
    ),
    # 4. 〜になります (presentation/existence instead of でございます)
    (
        re.compile(r"(こちら|そちら|これ|それ|お会計|資料|お茶|コーヒー)が?([^\s。、！？]{0,4}?)になります"),
        "「〜になります」の不適切な用法",
        "事物が変化するわけではないため、「〜でございます」を用います（例: 「資料でございます」）",
    ),
    # 5. 〜いただく形になります
    (
        re.compile(r"いただく形(になり|になりまして|になります)"),
        "「〜いただく形になります」の責任回避表現",
        "「〜をお願い申し上げます」または「〜していただきますようお願い申し上げます」と明確に伝えます",
    ),
]


class PragmaticsEngine:
    """Evaluates Japanese spoken pragmatics, sociolinguistic register fit, and business appropriateness."""

    def evaluate(self, text: str, ctx: SocialContext, register: Register | None = None) -> dict[str, Any]:
        target = register or ctx.register_target
        cleaned = text.strip() if text else ""

        # 1. Brown & Levinson Politeness Matrix (W = P + D + R)
        matrix = self._compute_politeness_matrix(ctx)

        # 2. Wakimae In-Group Humbling Verification (相対敬語)
        wakimae = self._verify_wakimae_rules(cleaned, ctx)

        # 3. Baito Keigo (バイト敬語) Detection
        baito_res = self._detect_baito_keigo(cleaned)

        # 4. Cushion Words (クッション言葉) Detection
        cushion_res = self._detect_cushion_words(cleaned, ctx)

        # 5. Over/Under-formal heuristic
        over_formal = False
        under_formal = False

        if ctx.relationship.value == "friendly" and ctx.familiarity_level >= 4 and target in (Register.BUSINESS_KEIGO, Register.VERY_FORMAL):
            if "でございます" in cleaned or "させていただきます" in cleaned or "申し上げます" in cleaned:
                over_formal = True

        if ctx.business_context and target == Register.TAMEGUCHI and ("だ" in cleaned and "です" not in cleaned and "ます" not in cleaned):
            under_formal = True

        # Check under-formal when speaking to Soto client
        if ctx.listener_group == Group.SOTO and target != Register.TAMEGUCHI:
            if re.search(r"(だよ|だね|じゃない|だろ|じゃん|ねえ)", cleaned):
                under_formal = True

        # 6. Synthesize Naturalness and Context-Fit Scores
        naturalness = 0.90
        context_fit = 0.92

        if over_formal:
            naturalness = min(naturalness, 0.58)
            context_fit = min(context_fit, 0.60)

        if under_formal:
            naturalness = min(naturalness, 0.55)
            context_fit = min(context_fit, 0.55)

        if wakimae["is_violation"]:
            naturalness = min(naturalness, 0.50)
            context_fit = min(context_fit, 0.45)

        if baito_res["found"]:
            naturalness = min(naturalness, 0.68)
            context_fit = min(context_fit, 0.70)

        if cushion_res["bonus_applied"]:
            context_fit = min(1.0, context_fit + 0.08)
            naturalness = min(1.0, naturalness + 0.05)

        if len(cleaned) > 80 and target == Register.TAMEGUCHI:
            naturalness = min(naturalness, 0.70)

        # Register fit calculation
        register_fit = 0.95
        if over_formal or under_formal:
            register_fit = 0.55
        elif baito_res["found"]:
            register_fit = 0.75
        elif wakimae["is_violation"]:
            register_fit = 0.50

        # Compile pedagogical notes
        notes: list[str] = []
        if wakimae["is_violation"] and wakimae["pedagogical_advice"]:
            notes.append(wakimae["pedagogical_advice"])
        if baito_res["found"] and baito_res["primary_suggestion"]:
            notes.append(f"⚠️ Phát hiện Baito Keigo: {baito_res['primary_suggestion']}")
        if cushion_res["bonus_applied"]:
            phrases = ", ".join(cushion_res["detected_phrases"])
            notes.append(f"✨ Điểm cộng: Sử dụng từ đệm khéo léo ({phrases})")
        elif matrix["ranking_of_imposition_R"] >= 4.0 and not cushion_res["found"]:
            notes.append("💡 Gợi ý: Thêm từ đệm (クッション言葉 như「恐れ入りますが」) giúp lời yêu cầu lịch thiệp hơn.")

        return {
            "over_formal": over_formal,
            "under_formal": under_formal,
            "naturalness": round(naturalness, 2),
            "register_fit": round(register_fit, 2),
            "context_fit": round(context_fit, 2),
            "wakimae": wakimae,
            "baito_keigo": baito_res,
            "cushion_words": cushion_res,
            "politeness_matrix": matrix,
            "pedagogical_notes": notes,
        }

    def _compute_politeness_matrix(self, ctx: SocialContext) -> dict[str, Any]:
        """Calculates Brown & Levinson's Politeness Weight: W = P + D + R."""
        # 1. Power Distance (P) [1.0 - 5.0]
        p_map = {
            PersonRole.CUSTOMER: 4.8,
            PersonRole.CLIENT: 4.8,
            PersonRole.EXECUTIVE: 4.5,
            PersonRole.MANAGER: 4.0,
            PersonRole.SALES_CONTACT: 3.8,
            PersonRole.PARTNER: 3.5,
            PersonRole.STRANGER: 3.2,
            PersonRole.COWORKER: 2.5,
            PersonRole.EMPLOYEE: 2.2,
            PersonRole.FRIEND: 1.0,
            PersonRole.FAMILY: 1.0,
        }
        P = p_map.get(ctx.listener_role, float(ctx.hierarchy_level))

        # 2. Social Distance (D) [1.0 - 5.0]
        # Inverted from familiarity: 1=stranger (D=5), 5=close (D=1)
        D = float(max(1, 6 - ctx.familiarity_level))
        if ctx.listener_group == Group.SOTO:
            D = max(D, 4.0)
        elif ctx.listener_group == Group.UCHI:
            D = min(D, 3.0)

        # 3. Ranking of Imposition (R) [1.0 - 5.0]
        r_map = {
            Situation.APOLOGY: 4.8,
            Situation.REQUEST: 4.5,
            Situation.SALES: 4.0,
            Situation.BUSINESS_MEETING: 3.5,
            Situation.PHONE: 3.5,
            Situation.EMAIL: 3.2,
            Situation.PRESENTATION: 3.0,
            Situation.INTRODUCTION: 2.5,
            Situation.RECEPTION: 2.5,
            Situation.CASUAL_CHAT: 1.2,
        }
        R = r_map.get(ctx.situation, 3.0)

        total_W = P + D + R

        if total_W >= 11.5:
            req_formality = "very_formal"
        elif total_W >= 8.5:
            req_formality = "business_keigo"
        elif total_W >= 5.5:
            req_formality = "polite"
        else:
            req_formality = "casual"

        return {
            "power_distance_P": round(P, 1),
            "social_distance_D": round(D, 1),
            "ranking_of_imposition_R": round(R, 1),
            "total_weight_W": round(total_W, 1),
            "required_formality": req_formality,
        }

    def _verify_wakimae_rules(self, text: str, ctx: SocialContext) -> dict[str, Any]:
        """Checks Japanese relative honorifics (相対敬語 / Wakimae).

        When speaking to Soto (external customer/client):
        - In-group referents (even superiors like CEO/Manager) must NEVER receive Sonkeigo or honorific titles (様, 社長).
        """
        if not text:
            return {"is_violation": False, "reason": None, "pedagogical_advice": None}

        listener_is_soto = ctx.listener_group == Group.SOTO or ctx.listener_role in (
            PersonRole.CUSTOMER,
            PersonRole.CLIENT,
            PersonRole.SALES_CONTACT,
            PersonRole.STRANGER,
        )

        referent_is_uchi = ctx.referent_group == Group.UCHI or ctx.referent_role in (
            PersonRole.SELF,
            PersonRole.MANAGER,
            PersonRole.EXECUTIVE,
            PersonRole.COWORKER,
            PersonRole.EMPLOYEE,
        )

        if listener_is_soto and referent_is_uchi and ctx.referent_role != PersonRole.SELF:
            # Check 1: In-group title violation (e.g. 社長様, 山田社長様, 社長の田中様, 部長様)
            title_match = re.search(r"(社長様|部長様|課長様|役員様|[^\s。、！？]{1,4}社長様?)", text)
            if title_match:
                offending = title_match.group(0)
                return {
                    "is_violation": True,
                    "reason": f"社外の相手に対し社内上司に敬称・役職敬称「{offending}」を使用しています",
                    "pedagogical_advice": (
                        "Lỗi Kính ngữ tương đối (相対敬語): Khi nói chuyện với khách hàng bên ngoài (Soto), "
                        "người trong công ty mình (kể cả Giám đốc) đều thuộc nhóm Uchi, phải bỏ chức danh '社長/様' "
                        "(ví dụ: dùng '社長の田中は外出しております', không dùng '田中社長様')."
                    ),
                }

            # Check 2: Using Sonkeigo for in-group action (e.g. 弊社社長がおっしゃいました, 田中はいらっしゃいません)
            uchi_sonkeigo_match = re.search(r"(弊社|当社|我が社|うちの社|社長の[^\s。、！？]{1,4}|[^\s。、！？]{1,4}部長)が?(おっしゃ|いらっしゃ|召し上が|ご覧にな|お見えにな)", text)
            if uchi_sonkeigo_match:
                offending = uchi_sonkeigo_match.group(0)
                return {
                    "is_violation": True,
                    "reason": f"社外の相手に対し社内人物の動作に尊敬語「{offending}」を使用しています",
                    "pedagogical_advice": (
                        "Lỗi Kính ngữ tương đối (相対敬語): Không dùng Tôn kính ngữ (Sonkeigo) cho hành động của người thuộc công ty mình trước mặt khách hàng. "
                        "Hãy dùng Khiêm nhường ngữ (Kenjougo) (ví dụ: dùng '申しました' thay vì 'おっしゃいました')."
                    ),
                }

        return {"is_violation": False, "reason": None, "pedagogical_advice": None}

    def _detect_baito_keigo(self, text: str) -> dict[str, Any]:
        """Detects commercial manual keigo (バイト敬語)."""
        issues: list[dict[str, str]] = []

        for pattern, rule_title, suggestion_tpl in BAITO_KEIGO_PATTERNS:
            match = pattern.search(text)
            if match:
                matched_str = match.group(0)
                stem = match.group(1) if match.groups() else ""
                particle = match.group(2) if len(match.groups()) >= 2 else ""

                # Special filter for directional 方
                if "方" in matched_str and stem in ("あちら", "そちら", "どちら", "北", "南", "東", "西", "右", "左", "前", "後"):
                    continue

                suggestion = suggestion_tpl.format(stem=stem, particle=particle)
                issues.append({
                    "pattern": rule_title,
                    "offending_phrase": matched_str,
                    "suggestion": suggestion,
                })

        primary_suggestion = issues[0]["suggestion"] if issues else None

        return {
            "found": len(issues) > 0,
            "issues": issues,
            "primary_suggestion": primary_suggestion,
        }

    def _detect_cushion_words(self, text: str, ctx: SocialContext) -> dict[str, Any]:
        """Identifies standard Japanese cushion words (クッション言葉)."""
        detected: list[str] = []

        for phrase in ALL_CUSHION_PHRASES:
            if phrase in text:
                detected.append(phrase)

        # Bonus applied when cushion word is used in high-imposition speech acts (Request, Refusal, Inquiry)
        high_imposition = ctx.situation in (Situation.REQUEST, Situation.APOLOGY, Situation.EMAIL, Situation.PHONE) or ctx.hierarchy_level >= 4
        bonus_applied = len(detected) > 0 and high_imposition

        return {
            "found": len(detected) > 0,
            "detected_phrases": detected,
            "count": len(detected),
            "bonus_applied": bonus_applied,
        }

