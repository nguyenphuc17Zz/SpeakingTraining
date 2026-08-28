import re
from typing import Any

from app.domains.shadowing.contracts import ExtractedGrammar, TranscriptSegmentDTO


class GrammarExtractor:
    """Extracts grammar constructions and spoken patterns with source span tracking."""

    # Common grammar rules and patterns
    _GRAMMAR_CATALOG = [
        ("〜わけではない", re.compile(r"(わけではない|わけじゃない)"), "N3", "Không hẳn là / không nhất thiết là..."),
        ("〜てしまう / ちゃう", re.compile(r"(てしまう|ちゃう|じゃう)"), "N4", "Lỡ / hoàn thành việc gì đó (khẩu ngữ)"),
        ("〜ておく / とく", re.compile(r"(ておく|とく|どく)"), "N4", "Làm sẵn việc gì đó trước"),
        ("〜ざるを得ない", re.compile(r"ざるを得ない"), "N2", "Đành phải / không thể không..."),
        ("〜にもかかわらず", re.compile(r"にもかかわらず"), "N2", "Mặc dù / bất chấp..."),
        ("〜に違いない", re.compile(r"に違いない"), "N3", "Chắc chắn là..."),
        ("〜なければならない / なきゃ", re.compile(r"(なければならない|なきゃ|なくちゃ)"), "N4", "Phải làm gì đó"),
        ("〜てはいけない / ちゃだめ", re.compile(r"(てはいけない|ちゃだめ|ちゃいけない)"), "N4", "Không được làm gì đó"),
        ("〜とおりに", re.compile(r"とおりに"), "N3", "Theo đúng như..."),
        ("〜おかげで", re.compile(r"おかげで"), "N3", "Nhờ có..."),
        ("〜せいで", re.compile(r"せいで"), "N3", "Tại vì / do lỗi của..."),
    ]

    @classmethod
    def extract_from_segments(
        cls,
        segments: list[TranscriptSegmentDTO],
        ai_extracted_items: list[dict[str, Any]] | None = None,
    ) -> dict[str, list[ExtractedGrammar]]:
        """
        Extracts grammar patterns mapped by segment_id.
        Integrates AI extracted grammar with deterministic regex rule matching.
        """
        results_by_seg: dict[str, list[ExtractedGrammar]] = {s.id: [] for s in segments}

        # 1. AI-extracted items
        if ai_extracted_items:
            for item in ai_extracted_items:
                seg_id = item.get("source_segment_id")
                pattern = item.get("pattern", "").strip()
                if not pattern:
                    continue

                grammar = ExtractedGrammar(
                    pattern=pattern,
                    level=item.get("level", "N3"),
                    meaning=item.get("meaning", "Mẫu ngữ pháp trong câu"),
                    context=item.get("context", ""),
                    example=item.get("example"),
                    source_segment_id=seg_id,
                    source_text_span=item.get("source_text_span", pattern),
                    learning_value=float(item.get("learning_value", 0.85)),
                )

                if seg_id and seg_id in results_by_seg:
                    results_by_seg[seg_id].append(grammar)
                else:
                    for seg in segments:
                        if pattern in seg.normalized_text or (grammar.source_text_span and grammar.source_text_span in seg.normalized_text):
                            grammar.source_segment_id = seg.id
                            results_by_seg[seg.id].append(grammar)
                            break

        # 2. Rule-based pattern matching
        for seg in segments:
            text = seg.normalized_text
            for pat_name, pat_regex, level, meaning in cls._GRAMMAR_CATALOG:
                m = pat_regex.search(text)
                if m:
                    # Check if already present
                    already = any(g.pattern == pat_name for g in results_by_seg[seg.id])
                    if not already:
                        results_by_seg[seg.id].append(
                            ExtractedGrammar(
                                pattern=pat_name,
                                level=level,
                                meaning=meaning,
                                context=text,
                                example=text,
                                source_segment_id=seg.id,
                                source_text_span=m.group(0),
                                learning_value=0.85,
                            )
                        )

        return results_by_seg
