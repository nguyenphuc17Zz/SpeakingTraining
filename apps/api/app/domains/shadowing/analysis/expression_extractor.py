import re
from typing import Any

from app.domains.shadowing.contracts import NaturalExpression, TranscriptSegmentDTO


class NaturalExpressionExtractor:
    """Extracts spoken Japanese nuances, fillers, slang, sentence endings, and discourse markers."""

    _EXPRESSION_RULES = [
        ("マジで", re.compile(r"マジで?"), "slang", "Thật á?! / Nghiêm túc luôn?!"),
        ("やばい", re.compile(r"(やばい|ヤバい|ヤバっ)"), "slang", "Kinh khủng / Đỉnh vãi / Nguy rồi"),
        ("ぶっちゃけ", re.compile(r"ぶっちゃけ"), "slang", "Nói thẳng ra là..."),
        ("〜じゃん", re.compile(r"じゃん"), "sentence_ending", "Đúng không nào / Chẳng phải sao"),
        ("〜っけ", re.compile(r"っけ"), "sentence_ending", "Ấy nhỉ / Có phải thế không nhỉ"),
        ("〜よね", re.compile(r"よね"), "sentence_ending", "Đúng vậy nhỉ (đồng tình nhẹ nhàng)"),
        ("なんか", re.compile(r"なんか"), "filler", "Kiểu như là / Có cảm giác là..."),
        ("とりあえず", re.compile(r"とりあえず"), "discourse_marker", "Trước mắt là / Tạm thời thì..."),
        ("というか", re.compile(r"というか"), "discourse_marker", "Hay nói đúng hơn là..."),
        ("なるほど", re.compile(r"なるほど"), "reaction", "Thì ra là vậy / Ra thế"),
        ("たしかに", re.compile(r"たしかに"), "reaction", "Đúng thật là như vậy"),
    ]

    @classmethod
    def extract_from_segments(
        cls,
        segments: list[TranscriptSegmentDTO],
        ai_extracted_items: list[dict[str, Any]] | None = None,
    ) -> dict[str, list[NaturalExpression]]:
        """
        Extracts natural spoken expressions mapped by segment_id.
        """
        results_by_seg: dict[str, list[NaturalExpression]] = {s.id: [] for s in segments}

        # 1. AI-extracted items
        if ai_extracted_items:
            for item in ai_extracted_items:
                seg_id = item.get("source_segment_id")
                expr = item.get("expression", "").strip()
                if not expr:
                    continue

                natural_item = NaturalExpression(
                    expression=expr,
                    reading=item.get("reading"),
                    meaning=item.get("meaning", "Biểu cảm giao tiếp tự nhiên"),
                    category=item.get("category", "expression"),
                    context_sentence=item.get("context_sentence", ""),
                    source_segment_id=seg_id,
                    source_text_span=item.get("source_text_span", expr),
                    learning_value=float(item.get("learning_value", 0.85)),
                )

                if seg_id and seg_id in results_by_seg:
                    results_by_seg[seg_id].append(natural_item)
                else:
                    for seg in segments:
                        if expr in seg.normalized_text:
                            natural_item.source_segment_id = seg.id
                            results_by_seg[seg.id].append(natural_item)
                            break

        # 2. Rule-based pattern matching
        for seg in segments:
            text = seg.normalized_text
            for expr_name, pat_regex, category, meaning in cls._EXPRESSION_RULES:
                m = pat_regex.search(text)
                if m:
                    already = any(e.expression == expr_name for e in results_by_seg[seg.id])
                    if not already:
                        results_by_seg[seg.id].append(
                            NaturalExpression(
                                expression=expr_name,
                                reading=None,
                                meaning=meaning,
                                category=category,
                                context_sentence=text,
                                source_segment_id=seg.id,
                                source_text_span=m.group(0),
                                learning_value=0.85,
                            )
                        )

        return results_by_seg
