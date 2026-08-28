import re
import unicodedata


class TranscriptNormalizer:
    """Normalizes raw YouTube / Whisper caption text into clean, spoken-Japanese format."""

    # Remove non-speech subtitle tags like [音楽], [Music], (笑), >>
    _ARTIFACT_PATTERNS = [
        re.compile(r"\[[\w\s\u3000-\u30FF\u4E00-\u9FFF]+\]"), # [音楽], [Applause]
        re.compile(r"\(笑\)"),
        re.compile(r"（笑）"),
        re.compile(r"【.*?】"),
        re.compile(r"^[>\s\-]+"), # leading '>> '
    ]

    # Duplicate punctuation
    _DUP_PUNCT_PATTERNS = [
        (re.compile(r"[!！]{2,}"), "！"),
        (re.compile(r"[\?？]{2,}"), "？"),
        (re.compile(r"[。\.]{2,}"), "。"),
        (re.compile(r"[、,]{2,}"), "、"),
        (re.compile(r"\s+"), " "),
    ]

    @classmethod
    def normalize_text(cls, raw_text: str) -> str:
        """Cleans and standardizes Japanese transcript lines while preserving linguistic meaning."""
        if not raw_text:
            return ""

        text = raw_text.strip()

        # Remove caption noise/artifacts
        for pat in cls._ARTIFACT_PATTERNS:
            text = pat.sub("", text)

        # Replace full-width alphanumeric to half-width, but keep Japanese kana/kanji intact
        text = unicodedata.normalize("NFKC", text)

        # Replace duplicate punctuations
        for pat, rep in cls._DUP_PUNCT_PATTERNS:
            text = pat.sub(rep, text)

        # Clean spaces around Japanese punctuation
        text = re.sub(r"\s*([。！？、])\s*", r"\1", text)
        text = text.strip()

        return text
