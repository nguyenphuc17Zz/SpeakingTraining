import re
from typing import Any

from app.domains.pronunciation.japanese.reading_resolver import JapaneseReadingResolver
from app.domains.shadowing.contracts import ExtractedVocabulary, TranscriptSegmentDTO


class VocabularyExtractor:
    """Extracts high-value spoken vocabulary with precise source span tracking."""

    # Common spoken compound keywords/roots
    _COMMON_CONTENT_PATTERNS = [
        re.compile(r"([一-龥]{2,4})"),  # Kanji compounds
        re.compile(r"([一-龥]+[ぁ-ん]{1,3})"), # Inflected verb/adjective stems
        re.compile(r"([ァ-ヴー]{3,8})"), # Katakana loanwords
    ]

    # Stopwords to filter out
    _STOPWORDS = {
        "これ", "それ", "あれ", "どれ", "ここ", "そこ", "あそこ",
        "私", "僕", "俺", "あなた", "こと", "もの", "ため", "よう",
        "今日", "昨日", "明日", "今", "前", "後", "中", "人", "方",
    }

    @classmethod
    def extract_from_segments(
        cls,
        segments: list[TranscriptSegmentDTO],
        ai_extracted_items: list[dict[str, Any]] | None = None,
    ) -> dict[str, list[ExtractedVocabulary]]:
        """
        Extracts vocabulary items mapped by segment_id.
        Combines AI-enriched semantic annotations with deterministic span matching.
        """
        results_by_seg: dict[str, list[ExtractedVocabulary]] = {s.id: [] for s in segments}

        # 1. Ingest AI-extracted items if available
        if ai_extracted_items:
            for item in ai_extracted_items:
                seg_id = item.get("source_segment_id")
                word = item.get("word", "").strip()
                if not word:
                    continue

                vocab = ExtractedVocabulary(
                    word=word,
                    reading=item.get("reading") or JapaneseReadingResolver.to_hiragana(word),
                    meaning=item.get("meaning", "Spoken Japanese expression"),
                    part_of_speech=item.get("part_of_speech", "word"),
                    difficulty=item.get("difficulty", "N3"),
                    frequency=item.get("frequency", "Common"),
                    context_sentence=item.get("context_sentence", ""),
                    source_segment_id=seg_id,
                    source_text_span=item.get("source_text_span", word),
                    learning_value=float(item.get("learning_value", 0.85)),
                )

                if seg_id and seg_id in results_by_seg:
                    results_by_seg[seg_id].append(vocab)
                else:
                    # Match to first segment containing the word
                    for seg in segments:
                        if word in seg.normalized_text:
                            vocab.source_segment_id = seg.id
                            vocab.context_sentence = seg.normalized_text
                            results_by_seg[seg.id].append(vocab)
                            break

        # 2. Heuristic extraction for any segments with 0 vocabulary
        for seg in segments:
            if results_by_seg[seg.id]:
                continue

            text = seg.normalized_text
            candidates = []
            for pat in cls._COMMON_CONTENT_PATTERNS:
                for match in pat.finditer(text):
                    w = match.group(1).strip()
                    if w and w not in cls._STOPWORDS and len(w) >= 2:
                        candidates.append((w, match.start(), match.end()))

            for w, start_idx, end_idx in candidates[:2]:
                reading = JapaneseReadingResolver.to_hiragana(w)
                results_by_seg[seg.id].append(
                    ExtractedVocabulary(
                        word=w,
                        reading=reading,
                        meaning=f"Từ vựng trong câu '{text[:15]}...'",
                        part_of_speech="noun/verb",
                        difficulty="N3",
                        context_sentence=text,
                        source_segment_id=seg.id,
                        source_text_span=w,
                        learning_value=0.75,
                    )
                )

        return results_by_seg
