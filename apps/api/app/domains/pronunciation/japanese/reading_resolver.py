import re
from typing import Any
from app.core.logging import logger

# Try initializing SudachiPy (Industry Standard Japanese Morphological Analyzer)
_sudachi_tokenizer = None
_SUDACHI_AVAILABLE = False

try:
    from sudachipy import dictionary, tokenizer
    _sudachi_dict = dictionary.Dictionary()
    _sudachi_tokenizer = _sudachi_dict.create()
    _sudachi_mode = tokenizer.Tokenizer.SplitMode.C
    _SUDACHI_AVAILABLE = True
    logger.info("[ReadingResolver] SudachiPy Japanese morphological analyzer successfully initialized.")
except Exception as e:
    logger.warning(f"[ReadingResolver] SudachiPy initialization failed: {e}. Checking pykakasi fallback...")

# Fallback to pykakasi if SudachiPy is unavailable
_kakasi = None
_PYKAKASI_AVAILABLE = False
if not _SUDACHI_AVAILABLE:
    try:
        import pykakasi
        _kakasi = pykakasi.kakasi()
        _PYKAKASI_AVAILABLE = True
    except Exception as e:
        logger.warning(f"[ReadingResolver] pykakasi fallback failed: {e}.")


class JapaneseReadingResolver:
    """
    High-precision Japanese Morphological Analyzer & Reading Resolver using SudachiPy.
    Supports atomic Kanji-only Ruby extraction, Okurigana separation, and Hiragana normalization.
    """

    _CACHE_HIRA: dict[str, str] = {}
    _CACHE_RUBY: dict[str, list[dict[str, str | None]]] = {}
    _KANJI_RE = re.compile(r"[\u4E00-\u9FAF\u3400-\u4DBF]")

    @classmethod
    def to_hiragana(cls, text: str) -> str:
        """Converts arbitrary Japanese text (Kanji/Katakana/Mixed) into canonical Hiragana."""
        if not text:
            return ""

        clean_text = text.strip()
        if clean_text in cls._CACHE_HIRA:
            return cls._CACHE_HIRA[clean_text]

        stripped = re.sub(r"[、。！？\s\.,!\?…・~〜]+", "", clean_text)
        if not stripped:
            return ""

        # Primary: SudachiPy
        if _SUDACHI_AVAILABLE and _sudachi_tokenizer:
            try:
                from sudachipy import tokenizer
                morphemes = _sudachi_tokenizer.tokenize(stripped, tokenizer.Tokenizer.SplitMode.C)
                hira_parts = []
                for m in morphemes:
                    r_kata = m.reading_form() or m.surface()
                    hira_parts.append(cls._katakana_to_hiragana(r_kata))
                res = "".join(hira_parts)
                cls._CACHE_HIRA[clean_text] = res
                return res
            except Exception as e:
                logger.warning(f"[ReadingResolver] SudachiPy to_hiragana failed for '{clean_text}': {e}")

        # Secondary fallback: pykakasi
        if _PYKAKASI_AVAILABLE and _kakasi:
            try:
                result = _kakasi.convert(stripped)
                hiragana_parts = [chunk.get("hira", "") for chunk in result]
                res = cls._katakana_to_hiragana("".join(hiragana_parts))
                cls._CACHE_HIRA[clean_text] = res
                return res
            except Exception as e:
                logger.warning(f"[ReadingResolver] pykakasi fallback failed for '{clean_text}': {e}")

        # Fallback: character-level katakana conversion
        fallback_str = cls._katakana_to_hiragana(stripped)
        cls._CACHE_HIRA[clean_text] = fallback_str
        return fallback_str

    @classmethod
    def to_ruby_chunks(cls, text: str) -> list[dict[str, str | None]]:
        """
        Converts Japanese text into structured Ruby tokens with PRECISE Okurigana separation:
        Only pure Kanji segments receive a Hiragana reading, while prefix/suffix kana (okurigana)
        and pure kana/punctuation words remain unannotated (reading=None).
        
        Example:
          '住んでみたい' -> [{'text': '住', 'reading': 'す'}, {'text': 'んでみたい', 'reading': None}]
          '話します' -> [{'text': '話', 'reading': 'はな'}, {'text': 'します', 'reading': None}]
          '日本語' -> [{'text': '日本語', 'reading': 'にほんご'}]
        """
        if not text:
            return []

        clean_text = text.strip()
        if clean_text in cls._CACHE_RUBY:
            return cls._CACHE_RUBY[clean_text]

        # Primary: SudachiPy with Okurigana Stripping
        if _SUDACHI_AVAILABLE and _sudachi_tokenizer:
            try:
                from sudachipy import tokenizer
                morphemes = _sudachi_tokenizer.tokenize(text, tokenizer.Tokenizer.SplitMode.C)
                raw_chunks: list[dict[str, str | None]] = []

                for m in morphemes:
                    surface = m.surface()
                    reading_kata = m.reading_form() or surface
                    raw_chunks.extend(cls._split_morpheme_okurigana(surface, reading_kata))

                merged_chunks = cls._merge_adjacent_plain_chunks(raw_chunks)
                cls._CACHE_RUBY[clean_text] = merged_chunks
                return merged_chunks
            except Exception as e:
                logger.warning(f"[ReadingResolver] SudachiPy to_ruby_chunks failed for '{text}': {e}")

        # Secondary fallback: pykakasi
        if _PYKAKASI_AVAILABLE and _kakasi:
            try:
                chunks = _kakasi.convert(text)
                ruby_result: list[dict[str, str | None]] = []
                for chunk in chunks:
                    orig = chunk.get("orig", "")
                    hira = chunk.get("hira", "")
                    if not orig:
                        continue
                    if cls._KANJI_RE.search(orig):
                        hira_norm = cls._katakana_to_hiragana(hira)
                        ruby_result.append({"text": orig, "reading": hira_norm})
                    else:
                        ruby_result.append({"text": orig, "reading": None})

                merged = cls._merge_adjacent_plain_chunks(ruby_result)
                cls._CACHE_RUBY[clean_text] = merged
                return merged
            except Exception as e:
                logger.warning(f"[ReadingResolver] pykakasi to_ruby_chunks fallback failed for '{text}': {e}")

        return [{"text": text, "reading": None}]

    @classmethod
    def _split_morpheme_okurigana(cls, surface: str, reading_kata: str) -> list[dict[str, str | None]]:
        """
        Strips common leading/trailing kana between surface and reading,
        ensuring furigana is placed ONLY over the Kanji root.
        """
        reading_hira = cls._katakana_to_hiragana(reading_kata)

        # If no Kanji in surface, no ruby needed
        if not cls._KANJI_RE.search(surface):
            return [{"text": surface, "reading": None}]

        # Strip leading common Kana (prefix)
        p_len = 0
        while (
            p_len < len(surface)
            and p_len < len(reading_hira)
            and surface[p_len] == reading_hira[p_len]
            and not cls._KANJI_RE.search(surface[p_len])
        ):
            p_len += 1

        prefix = surface[:p_len]
        rem_surface = surface[p_len:]
        rem_reading = reading_hira[p_len:]

        # Strip trailing common Kana (suffix / okurigana)
        s_len = 0
        while (
            s_len < len(rem_surface)
            and s_len < len(rem_reading)
            and rem_surface[-(s_len + 1)] == rem_reading[-(s_len + 1)]
            and not cls._KANJI_RE.search(rem_surface[-(s_len + 1)])
        ):
            s_len += 1

        suffix = rem_surface[len(rem_surface) - s_len :] if s_len > 0 else ""
        kanji_part = rem_surface[: len(rem_surface) - s_len] if s_len > 0 else rem_surface
        kanji_reading = rem_reading[: len(rem_reading) - s_len] if s_len > 0 else rem_reading

        res: list[dict[str, str | None]] = []
        if prefix:
            res.append({"text": prefix, "reading": None})
        if kanji_part:
            res.append({"text": kanji_part, "reading": kanji_reading})
        if suffix:
            res.append({"text": suffix, "reading": None})

        return res

    @classmethod
    def _merge_adjacent_plain_chunks(cls, chunks: list[dict[str, str | None]]) -> list[dict[str, str | None]]:
        """Merges consecutive chunks that have reading=None into a single clean string token."""
        if not chunks:
            return []

        merged: list[dict[str, str | None]] = []
        current_plain = ""

        for c in chunks:
            if c.get("reading") is None:
                current_plain += c.get("text", "")
            else:
                if current_plain:
                    merged.append({"text": current_plain, "reading": None})
                    current_plain = ""
                merged.append(c)

        if current_plain:
            merged.append({"text": current_plain, "reading": None})

        return merged

    @staticmethod
    def _katakana_to_hiragana(text: str) -> str:
        """Converts Katakana characters (0x30A1 - 0x30F6) to Hiragana using offset (0x60)."""
        res = []
        for char in text:
            code = ord(char)
            if 0x30A1 <= code <= 0x30F6:
                res.append(chr(code - 0x60))
            else:
                res.append(char)
        return "".join(res)

    @classmethod
    def normalize_sentence(cls, text: str) -> dict[str, Any]:
        """Provides full linguistic normalized view: original, hiragana, character count, cleaned."""
        hiragana = cls.to_hiragana(text)
        return {
            "original": text,
            "hiragana": hiragana,
            "char_count": len(hiragana),
        }
