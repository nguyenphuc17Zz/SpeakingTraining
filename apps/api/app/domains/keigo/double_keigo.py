"""DoubleKeigoAnalyzer — nuanced morphological classification, avoiding false positives."""

from __future__ import annotations

import re
from typing import Any

# Established double keigo forms customary and widely accepted in standard Japanese
ACCEPTED_ESTABLISHED = {
    "お召し上がりになる",
    "お召し上がりください",
    "お召し上がりになります",
    "お召し上がりになりました",
    "お休みになる",
    "お休みください",
    "お休みなさい",
    "ご覧になる",
    "ご覧ください",
    "ご覧になります",
    "ご覧になりました",
    "ご覧いただきます",
    "お目にかかる",
    "お目にかかります",
    "お目にかかりました",
    "お伺いする",
    "お伺いします",
    "お伺いいたします",
    "お伺いしました",
    "お越しになる",
    "お越しください",
    "お越しになります",
    "お越しいただきました",
    "お見えになる",
    "お見えになります",
    "お見えになりました",
    "拝見いたします",
    "拝見します",
    "拝見いたしました",
    "ご案内いたします",
    "ご案内申し上げます",
    "ご説明いたします",
    "ご説明申し上げます",
    "ご報告いたします",
    "ご報告申し上げます",
    "ご用意いたします",
    "ご用意いたしました",
}

# Nonstandard double-keigo patterns with specific suggestions
NONSTANDARD_DOUBLE_KEIGO: list[tuple[re.Pattern, str, str]] = [
    # 1. お〜になられる (Sonkeigo お〜になる + られる)
    (
        re.compile(r"お([^\s。、！？]{1,6}?)になられ(る|ます|た|て|ない)?"),
        "二重敬語 (お〜になる + られる)",
        "「お{stem}になる」または「{stem}られる」の一方のみを用います",
    ),
    # 2. ご〜になられる (Sonkeigo ご〜になる + られる)
    (
        re.compile(r"ご([^\s。、！？]{1,6}?)になられ(る|ます|た|て|ない)?"),
        "二重敬語 (ご〜になる + られる)",
        "「ご{stem}になる」または「ご{stem}なさる」を用います",
    ),
    # 3. おっしゃられる (おっしゃる + られる)
    (
        re.compile(r"おっしゃられ(る|ます|た|て|ない)?"),
        "二重敬語 (おっしゃる + られる)",
        "「おっしゃる / おっしゃいます」を用います（すでに尊敬語です）",
    ),
    # 4. いらっしゃられる (いらっしゃる + られる)
    (
        re.compile(r"いらっしゃられ(る|ます|た|て|ない)?"),
        "二重敬語 (いらっしゃる + られる)",
        "「いらっしゃる / いらっしゃいます」を用います",
    ),
    # 5. 参上される (参上する(謙譲) + される(尊敬) - 方向矛盾)
    (
        re.compile(r"参上され(る|ます|た|て)?"),
        "敬語の混同 (謙譲語「参上」+ 尊敬語「される」)",
        "相手の動作なら「お越しになる/いらっしゃる」、自分の動作なら「参上する/伺う」を用います",
    ),
    # 6. 拝見される (拝見する(謙譲) + される(尊敬) - 方向矛盾)
    (
        re.compile(r"拝見され(る|ます|た|て)?"),
        "敬語の混同 (謙譲語「拝見」+ 尊敬語「される」)",
        "相手がご覧になる場合は「ご覧になる」、自分が見る場合は「拝見する」を用います",
    ),
    # 7. お見えになられる (お見えになる + られる)
    (
        re.compile(r"お見えになられ(る|ます|た|て)?"),
        "二重敬語 (お見えになる + られる)",
        "「お見えになる / お見えになりました」を用います",
    ),
    # 8. お越しになられる (お越しになる + られる)
    (
        re.compile(r"お越しになられ(る|ます|た|て)?"),
        "二重敬語 (お越しになる + られる)",
        "「お越しになる / お越しになりました」を用います",
    ),
    # 9. 伺わさせていただく (伺う(謙譲) + させていただく(謙譲))
    (
        re.compile(r"伺(わ|わせ|わせて)?いただき(ます|ました)?"),
        "過剰な謙譲語の重複 (伺う + させていただく)",
        "「伺います」または「お伺いいたします」を用います",
    ),
    # 10. ご拝読 / お拝見 (謙譲名詞への美化接頭辞付加)
    (
        re.compile(r"(ご拝読|お拝見|ご拝聴)"),
        "過剰修飾 (謙譲語への「お/ご」付加)",
        "「拝読」「拝見」「拝聴」のみを用います",
    ),
]


class DoubleKeigoAnalyzer:
    """Analyzes Japanese honorific expressions for grammatical double-keigo (二重敬語).

    Targets morphological predicate structures instead of naive character counts,
    eliminating false positives on natural polite speech containing multiple お/ご.
    """

    def analyze(self, text: str) -> dict[str, Any]:
        if not text:
            return {
                "category": "double_keigo",
                "status": "none",
                "severity": "none",
                "confidence": 1.0,
                "is_double_keigo": False,
                "offending_phrase": None,
                "rule": None,
                "recommendation": None,
            }

        cleaned = text.strip()

        # 1. Whitelist check for established customary expressions
        for established in ACCEPTED_ESTABLISHED:
            if established in cleaned:
                # If exact or contains accepted form, check if it also has a nonstandard pattern
                pass

        # 2. Check targeted nonstandard double-keigo patterns
        for pattern, rule_name, recommendation_tpl in NONSTANDARD_DOUBLE_KEIGO:
            match = pattern.search(cleaned)
            if match:
                matched_str = match.group(0)
                # Check if it was part of an accepted established expression
                if any(matched_str in est for est in ACCEPTED_ESTABLISHED):
                    continue

                stem = match.group(1) if match.groups() else ""
                recommendation = recommendation_tpl.format(stem=stem)
                return {
                    "category": "double_keigo",
                    "status": "generally_inappropriate",
                    "severity": "major",
                    "confidence": 0.95,
                    "is_double_keigo": True,
                    "offending_phrase": matched_str,
                    "rule": rule_name,
                    "recommendation": recommendation,
                }

        # 3. Check borderline patterns (e.g. お[動詞]される like お話しされる)
        borderline_match = re.search(r"お([^\s。、！？]{2,4})され(る|ます|た)?", cleaned)
        if borderline_match:
            stem = borderline_match.group(1)
            # Exclude common passive / potential or non-keigo verbs
            if stem not in ("世話", "待た", "邪魔", "願", "任せ"):
                return {
                    "category": "double_keigo",
                    "status": "context_dependent",
                    "severity": "minor",
                    "confidence": 0.75,
                    "is_double_keigo": True,
                    "offending_phrase": borderline_match.group(0),
                    "rule": "「お〜される」の形 (慣用化しつつあるが「お〜になる」がより適切)",
                    "recommendation": f"「お{stem}になる」を用いると、より洗練された印象になります",
                }

        # Clean, natural sentence — no double keigo detected
        return {
            "category": "double_keigo",
            "status": "none",
            "severity": "none",
            "confidence": 0.90,
            "is_double_keigo": False,
            "offending_phrase": None,
            "rule": None,
            "recommendation": None,
        }

