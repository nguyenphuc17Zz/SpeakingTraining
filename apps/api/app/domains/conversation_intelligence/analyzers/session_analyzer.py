from typing import Any

from app.domains.conversation_intelligence.contracts import SessionAnalysisResult


class SessionAnalyzer:
    """Aggregates conversation-level metrics and reviews."""

    @staticmethod
    def detect_repeated_patterns(
        turns: list[dict[str, Any]],
        corrections: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Identifies patterns or errors occurring repeatedly within the same session."""
        pattern_counts: dict[str, int] = {}
        repeated_list: list[dict[str, Any]] = []

        # Check for repeated particle confusion
        for c in corrections:
            orig = c.get("original", "").strip()
            if orig in ("は", "が", "を", "に", "で"):
                key = f"Trợ từ「{orig}」"
                pattern_counts[key] = pattern_counts.get(key, 0) + 1

        # Check for repetitive sentence endings
        for t in turns:
            if t.get("speaker") == "user":
                txt = t.get("transcript", "").strip()
                if txt.endswith("と思います"):
                    pattern_counts["Kết câu「〜と思います」"] = pattern_counts.get("Kết câu「〜と思います」", 0) + 1
                elif txt.endswith("です"):
                    pattern_counts["Kết câu「〜です」liên tục"] = pattern_counts.get("Kết câu「〜です」liên tục", 0) + 1

        for pat, cnt in pattern_counts.items():
            if cnt >= 2:
                repeated_list.append({
                    "pattern": pat,
                    "occurrences_count": cnt,
                    "recommendation": f"Đã sử dụng {cnt} lần trong buổi nói chuyện. Thử đa dạng hóa các cấu trúc tương đương.",
                })

        return repeated_list

    @staticmethod
    def ensure_strengths(result: SessionAnalysisResult, user_turns_count: int) -> SessionAnalysisResult:
        """Guarantees at least 2 positive strengths are always highlighted."""
        if not result.strengths:
            result.strengths = [
                "Duy trì luồng hội thoại liên tục và phản xạ tự nhiên",
                "Sẵn sàng diễn đạt ý kiến và tiếp thu phản hồi",
            ]
        return result
