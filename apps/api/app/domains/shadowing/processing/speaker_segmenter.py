import re
from app.domains.shadowing.contracts import TranscriptSegmentDTO


class SpeakerSegmenter:
    """Assigns consistent speaker identifiers (Speaker A, Speaker B, Narrator) across transcript segments."""

    _SPEAKER_PREFIX_RE = re.compile(r"^([A-Za-z0-9\u3040-\u30FF\u4E00-\u9FFF]+)[:：]\s*")

    @classmethod
    def segment_speakers(
        cls,
        segments: list[TranscriptSegmentDTO],
    ) -> list[TranscriptSegmentDTO]:
        """
        Infers or standardizes speaker IDs without hallucinating personal demographics.
        """
        if not segments:
            return []

        speaker_map: dict[str, str] = {}
        speaker_counter = 0

        for seg in segments:
            text = seg.normalized_text

            # Check explicit prefix: e.g. "田中: おはようございます" or "A: こんにちは"
            match = cls._SPEAKER_PREFIX_RE.match(text)
            if match:
                raw_speaker = match.group(1).strip()
                if raw_speaker not in speaker_map:
                    speaker_counter += 1
                    speaker_map[raw_speaker] = f"Speaker {chr(64 + speaker_counter)}" if speaker_counter <= 26 else f"Speaker {speaker_counter}"

                seg.speaker_id = speaker_map[raw_speaker]
                # Strip speaker prefix from normalized text
                seg.normalized_text = cls._SPEAKER_PREFIX_RE.sub("", text).strip()
            else:
                # Default speaker if no explicit tag
                seg.speaker_id = "Speaker A"

        return segments
