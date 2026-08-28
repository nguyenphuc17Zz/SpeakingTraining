from app.domains.pronunciation.contracts import MoraUnit
from app.domains.pronunciation.japanese.reading_resolver import JapaneseReadingResolver


# Phoneme mappings for standard Japanese kana
KANA_PHONEMES: dict[str, list[str]] = {
    # Vowels
    "あ": ["a"], "い": ["i"], "う": ["u"], "え": ["e"], "お": ["o"],
    # K-line
    "か": ["k", "a"], "き": ["k", "i"], "く": ["k", "u"], "け": ["k", "e"], "こ": ["k", "o"],
    # G-line
    "が": ["g", "a"], "ぎ": ["g", "i"], "ぐ": ["g", "u"], "げ": ["g", "e"], "ご": ["g", "o"],
    # S-line
    "さ": ["s", "a"], "し": ["sh", "i"], "す": ["s", "u"], "せ": ["s", "e"], "そ": ["s", "o"],
    # Z-line
    "ざ": ["z", "a"], "じ": ["j", "i"], "ず": ["z", "u"], "ぜ": ["z", "e"], "ぞ": ["z", "o"],
    # T-line
    "た": ["t", "a"], "ち": ["ch", "i"], "つ": ["ts", "u"], "て": ["t", "e"], "と": ["t", "o"],
    # D-line
    "だ": ["d", "a"], "ぢ": ["j", "i"], "づ": ["z", "u"], "で": ["d", "e"], "ど": ["d", "o"],
    # N-line
    "な": ["n", "a"], "に": ["n", "i"], "ぬ": ["n", "u"], "ね": ["n", "e"], "の": ["n", "o"],
    # H-line
    "は": ["h", "a"], "ひ": ["h", "i"], "ふ": ["f", "u"], "へ": ["h", "e"], "ほ": ["h", "o"],
    # B-line
    "ば": ["b", "a"], "び": ["b", "i"], "ぶ": ["b", "u"], "べ": ["b", "e"], "ぼ": ["b", "o"],
    # P-line
    "ぱ": ["p", "a"], "ぴ": ["p", "i"], "ぷ": ["p", "u"], "ぺ": ["p", "e"], "ぽ": ["p", "o"],
    # M-line
    "ま": ["m", "a"], "み": ["m", "i"], "む": ["m", "u"], "め": ["m", "e"], "も": ["m", "o"],
    # Y-line
    "や": ["j", "a"], "ゆ": ["j", "u"], "よ": ["j", "o"],
    # R-line
    "ら": ["r", "a"], "り": ["r", "i"], "る": ["r", "u"], "れ": ["r", "e"], "ろ": ["r", "o"],
    # W-line
    "わ": ["w", "a"], "を": ["o"],
    # Special morae
    "ん": ["N"],
    "っ": ["Q"],
    "ー": [":"],
}

# Contracted sounds (Yōon)
YOON_PHONEMES: dict[str, list[str]] = {
    "きゃ": ["k", "j", "a"], "きゅ": ["k", "j", "u"], "きょ": ["k", "j", "o"],
    "ぎゃ": ["g", "j", "a"], "ぎゅ": ["g", "j", "u"], "ぎょ": ["g", "j", "o"],
    "しゃ": ["sh", "a"], "しゅ": ["sh", "u"], "しょ": ["sh", "o"],
    "じゃ": ["j", "a"], "じゅ": ["j", "u"], "じょ": ["j", "o"],
    "ちゃ": ["ch", "a"], "ちゅ": ["ch", "u"], "ちょ": ["ch", "o"],
    "にゃ": ["n", "j", "a"], "にゅ": ["n", "j", "u"], "にょ": ["n", "j", "o"],
    "ひゃ": ["h", "j", "a"], "ひゅ": ["h", "j", "u"], "ひょ": ["h", "j", "o"],
    "びゃ": ["b", "j", "a"], "びゅ": ["b", "j", "u"], "びょ": ["b", "j", "o"],
    "ぴゃ": ["p", "j", "a"], "ぴゅ": ["p", "j", "u"], "ぴょ": ["p", "j", "o"],
    "みゃ": ["m", "j", "a"], "みゅ": ["m", "j", "u"], "みょ": ["m", "j", "o"],
    "りゃ": ["r", "j", "a"], "りゅ": ["r", "j", "u"], "りょ": ["r", "j", "o"],
}

SMALL_KANA = {"ゃ", "ゅ", "ょ", "ぁ", "ぃ", "ぅ", "ぇ", "ぉ", "ゎ"}


class JapaneseMoraAnalyzer:
    """Accurately analyzes Japanese Hiragana strings into discrete mora units with phonemic data."""

    @classmethod
    def segment_moras(cls, text_or_hiragana: str) -> list[MoraUnit]:
        """Segments input text (Kanji or Kana) into an ordered list of MoraUnit objects."""
        # 1. Convert to Hiragana if not already
        hiragana = JapaneseReadingResolver.to_hiragana(text_or_hiragana)
        if not hiragana:
            return []

        moras: list[MoraUnit] = []
        i = 0
        n = len(hiragana)
        mora_idx = 0

        while i < n:
            curr_char = hiragana[i]
            next_char = hiragana[i + 1] if i + 1 < n else ""

            # Check for Yōon digraph (e.g. き + ゃ -> きゃ)
            if next_char in SMALL_KANA:
                combo = curr_char + next_char
                phonemes = YOON_PHONEMES.get(combo, [curr_char, next_char])
                moras.append(
                    MoraUnit(
                        mora_index=mora_idx,
                        kana=combo,
                        phonemes=phonemes,
                        is_special=True,
                        special_type="contracted",
                    )
                )
                i += 2
                mora_idx += 1
                continue

            # Check for Sokuon (っ)
            if curr_char == "っ":
                moras.append(
                    MoraUnit(
                        mora_index=mora_idx,
                        kana="っ",
                        phonemes=["Q"],
                        is_special=True,
                        special_type="gemination",
                    )
                )
                i += 1
                mora_idx += 1
                continue

            # Check for Hatsuon (ん)
            if curr_char == "ん":
                moras.append(
                    MoraUnit(
                        mora_index=mora_idx,
                        kana="ん",
                        phonemes=["N"],
                        is_special=True,
                        special_type="nasal",
                    )
                )
                i += 1
                mora_idx += 1
                continue

            # Check for Chōonpu (ー) or prolonged vowel in Hiragana
            if curr_char == "ー":
                moras.append(
                    MoraUnit(
                        mora_index=mora_idx,
                        kana="ー",
                        phonemes=[":"],
                        is_special=True,
                        special_type="long_vowel",
                    )
                )
                i += 1
                mora_idx += 1
                continue

            # Check if this vowel acts as long vowel extension (e.g. おばあさん -> あ extends ば; がっこう -> う extends こ)
            is_long_vowel_extension = False
            if mora_idx > 0 and curr_char in {"あ", "い", "う", "え", "お"}:
                prev_mora = moras[-1].kana
                # Standard Japanese long vowel pairings:
                # a + a (おばあさん), i + i (おじいさん), u + u (つうきん), e + e or e + i (せんせい), o + o or o + u (がっこう)
                if (
                    (curr_char == "あ" and prev_mora[-1] in {"か", "が", "さ", "ざ", "た", "だ", "な", "は", "ば", "ぱ", "ま", "や", "ら", "わ", "あ", "ゃ", "ぁ"})
                    or (curr_char == "い" and prev_mora[-1] in {"き", "ぎ", "し", "じ", "ち", "ぢ", "に", "ひ", "び", "ぴ", "み", "り", "い", "え", "け", "げ", "せ", "ぜ", "て", "で", "ね", "へ", "べ", "ぺ", "め", "れ", "ぃ", "ぇ"})
                    or (curr_char == "う" and prev_mora[-1] in {"く", "ぐ", "す", "ず", "つ", "づ", "ぬ", "ふ", "ぶ", "ぷ", "む", "ゆ", "る", "う", "お", "こ", "ご", "そ", "ぞ", "と", "ど", "の", "ほ", "ぼ", "ぽ", "も", "よ", "ろ", "ゅ", "ょ", "ぅ", "ぉ"})
                    or (curr_char == "え" and prev_mora[-1] in {"え", "け", "げ", "せ", "ぜ", "て", "で", "ね", "へ", "べ", "ぺ", "め", "れ", "ぇ"})
                    or (curr_char == "お" and prev_mora[-1] in {"お", "こ", "ご", "そ", "ぞ", "と", "ど", "の", "ほ", "ぼ", "ぽ", "も", "よ", "ろ", "ょ", "ぉ"})
                ):
                    is_long_vowel_extension = True

            phonemes = KANA_PHONEMES.get(curr_char, [curr_char])
            moras.append(
                MoraUnit(
                    mora_index=mora_idx,
                    kana=curr_char,
                    phonemes=phonemes,
                    is_special=is_long_vowel_extension,
                    special_type="long_vowel" if is_long_vowel_extension else None,
                )
            )
            i += 1
            mora_idx += 1

        return moras

    @classmethod
    def get_mora_count(cls, text: str) -> int:
        """Returns total mora count for a word or sentence."""
        return len(cls.segment_moras(text))
