import re
import uuid
from typing import Any

from app.domains.pronunciation.japanese.reading_resolver import JapaneseReadingResolver
from app.domains.shadowing.contracts import TranscriptSegmentDTO
from app.domains.shadowing.processing.normalizer import TranscriptNormalizer


class SentenceSegmenter:
    """
    Transforms raw YouTube/Whisper subtitle entries into clean, sentence-level
    shadowing segments with readings and precise timing boundaries.
    """

    # Sentence terminal punctuation
    _SENTENCE_END_RE = re.compile(r"([。！？\!\?]+)")

    @classmethod
    def segment_transcript(
        cls,
        raw_entries: list[dict[str, Any]],
        video_id: str,
    ) -> list[TranscriptSegmentDTO]:
        """
        Segments, merges, and normalizes transcript entries into coherent sentence units.
        """
        if not raw_entries:
            return []

        # 1. Normalize all text and compute boundaries
        cleaned_entries: list[dict[str, Any]] = []
        for entry in raw_entries:
            raw_text = entry.get("text", "")
            norm_text = TranscriptNormalizer.normalize_text(raw_text)
            if not norm_text:
                continue

            start_t = float(entry.get("start", 0.0))
            end_t = float(entry.get("end", start_t + float(entry.get("duration", 2.0))))
            cleaned_entries.append({
                "original_text": raw_text,
                "normalized_text": norm_text,
                "start": start_t,
                "end": max(start_t + 0.5, end_t),
            })

        if not cleaned_entries:
            return []

        # 2. Merge short adjacent fragments (< 1.8s or no terminal punctuation)
        merged_units: list[dict[str, Any]] = []
        curr = cleaned_entries[0].copy()

        for next_entry in cleaned_entries[1:]:
            curr_text = curr["normalized_text"]
            curr_dur = curr["end"] - curr["start"]
            gap = next_entry["start"] - curr["end"]

            has_terminal = bool(cls._SENTENCE_END_RE.search(curr_text))

            # Merge condition:
            # - No sentence-ending punctuation AND (current segment is short < 6.0s) AND (pause is small < 1.2s)
            # OR current segment is very short (< 1.5s)
            should_merge = (
                (not has_terminal and curr_dur < 6.0 and gap < 1.2)
                or (curr_dur < 1.5 and gap < 1.5)
            )

            if should_merge and (curr["end"] - curr["start"] + (next_entry["end"] - next_entry["start"])) <= 14.0:
                curr["normalized_text"] = curr_text + (" " if curr_text.endswith(tuple("abcdefghijklmnopqrstuvwxyz")) else "") + next_entry["normalized_text"]
                curr["original_text"] = curr["original_text"] + " " + next_entry["original_text"]
                curr["end"] = next_entry["end"]
            else:
                merged_units.append(curr)
                curr = next_entry.copy()

        merged_units.append(curr)

        # 3. Create canonical TranscriptSegmentDTO items with readings
        results: list[TranscriptSegmentDTO] = []
        for idx, unit in enumerate(merged_units):
            norm_text = unit["normalized_text"].strip()
            if not norm_text:
                continue

            start_t = round(unit["start"], 2)
            end_t = round(unit["end"], 2)
            dur = round(end_t - start_t, 2)

            # Resolve reading and ruby structure using JapaneseReadingResolver
            try:
                reading = JapaneseReadingResolver.to_hiragana(norm_text)
                ruby = JapaneseReadingResolver.to_ruby_chunks(norm_text)
            except Exception:
                reading = norm_text
                ruby = [{"text": norm_text, "reading": None}]

            seg_id = f"seg_{uuid.uuid4().hex[:12]}"

            results.append(
                TranscriptSegmentDTO(
                    id=seg_id,
                    video_id=video_id,
                    start_time=start_t,
                    end_time=end_t,
                    duration=dur,
                    text=unit["original_text"],
                    normalized_text=norm_text,
                    reading=reading,
                    ruby=ruby,
                    language="ja",
                    confidence=1.0,
                    speaker_id="Speaker A",
                    sequence=idx,
                )
            )

        return results
