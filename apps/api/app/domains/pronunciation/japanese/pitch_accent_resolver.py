from typing import Any
from app.domains.pronunciation.contracts import PitchAccentPattern
from app.domains.pronunciation.japanese.mora_analyzer import JapaneseMoraAnalyzer
from app.domains.pronunciation.japanese.reading_resolver import JapaneseReadingResolver


# Standard Tokyo Pitch Accent Reference Lexicon for core Japanese vocabulary & patterns
# (Pattern: (mora_pattern, accent_kernel_index))
# 0 = Heiban (L H H H...), 1 = Atamadaka (H L L L...), 2 = Nakadaka (L H L L...), etc.
STANDARD_PITCH_LEXICON: dict[str, tuple[PitchAccentPattern, int]] = {
    # Nouns
    "きょう": (PitchAccentPattern.ATAMADAKA, 1),
    "あした": (PitchAccentPattern.NAKADAKA, 3),
    "きのう": (PitchAccentPattern.NAKADAKA, 2),
    "あめ": (PitchAccentPattern.ATAMADAKA, 1),       # 雨 (rain) = 1 [H L]
    "あめ (candy)": (PitchAccentPattern.HEIBAN, 0),  # 飴 (candy) = 0 [L H]
    "はし (bridge)": (PitchAccentPattern.ODAKA, 2),   # 橋 (bridge) = 2 [L H (drop on particle)]
    "はし (chopsticks)": (PitchAccentPattern.ATAMADAKA, 1), # 箸 = 1 [H L]
    "はし (edge)": (PitchAccentPattern.HEIBAN, 0),    # 端 = 0 [L H]
    "がっこう": (PitchAccentPattern.HEIBAN, 0),      # 学校 = 0 [L H H H]
    "せんせい": (PitchAccentPattern.NAKADAKA, 3),    # 先生 = 3 [L H H L]
    "にほんご": (PitchAccentPattern.HEIBAN, 0),      # 日本語 = 0 [L H H H]
    "えいが": (PitchAccentPattern.ATAMADAKA, 1),      # 映画 = 1 [H L L]
    "しんぶん": (PitchAccentPattern.HEIBAN, 0),      # 新聞 = 0 [L H H H]
    "ともだち": (PitchAccentPattern.HEIBAN, 0),      # 友達 = 0 [L H H H]
    "ほん": (PitchAccentPattern.ATAMADAKA, 1),        # 本 = 1 [H L]
    "みず": (PitchAccentPattern.HEIBAN, 0),          # 水 = 0 [L H]
    "くるま": (PitchAccentPattern.HEIBAN, 0),        # 車 = 0 [L H H]
    "いぬ": (PitchAccentPattern.NAKADAKA, 2),        # 犬 = 2 [L H]
    "ねこ": (PitchAccentPattern.ATAMADAKA, 1),        # 猫 = 1 [H L]
    "おばさん": (PitchAccentPattern.NAKADAKA, 2),    # 伯母さん = 2 [L H L L]
    "おばあさん": (PitchAccentPattern.NAKADAKA, 2),  # お祖母さん = 2 [L H L L L]
    "きって": (PitchAccentPattern.HEIBAN, 0),        # 切手 = 0 [L H H]
    "きて": (PitchAccentPattern.ATAMADAKA, 1),        # 来て = 1 [H L]
    "ごはん": (PitchAccentPattern.ATAMADAKA, 1),      # ご飯 = 1 [H L L]
    "さかな": (PitchAccentPattern.HEIBAN, 0),        # 魚 = 0 [L H H]

    # Verbs / Phrases
    "たべます": (PitchAccentPattern.NAKADAKA, 3),    # 食べます = 3 [L H H L]
    "のみます": (PitchAccentPattern.NAKADAKA, 3),    # 飲みます = 3 [L H H L]
    "いきます": (PitchAccentPattern.NAKADAKA, 3),    # 行きます = 3 [L H H L]
    "みます": (PitchAccentPattern.NAKADAKA, 2),      # 見ます = 2 [L H L]
    "みました": (PitchAccentPattern.NAKADAKA, 2),    # 見ました = 2 [L H L L]
    "ありがとう": (PitchAccentPattern.NAKADAKA, 2),  # ありがとう = 2 [L H L L L]
    "こんにちは": (PitchAccentPattern.HEIBAN, 0),    # こんにちは = 0 [L H H H H]
    "おはよう": (PitchAccentPattern.NAKADAKA, 2),    # おはよう = 2 [L H L L]
}


class PitchAccentTargetResolver:
    """Resolves expected Tokyo Japanese Pitch Accent patterns for target utterances."""

    @classmethod
    def resolve_target(cls, text: str) -> tuple[PitchAccentPattern, int, list[str]]:
        """
        Returns:
            - Pattern Enum (HEIBAN, ATAMADAKA, NAKADAKA, ODAKA)
            - Accent kernel index (0 for Heiban, 1 for Atamadaka, >1 for Nakadaka/Odaka)
            - Mora-level expected relative pitch list (['L', 'H', 'H', ...])
        """
        hiragana = JapaneseReadingResolver.to_hiragana(text)
        moras = JapaneseMoraAnalyzer.segment_moras(hiragana)
        mora_count = len(moras)
        if mora_count == 0:
            return PitchAccentPattern.UNKNOWN, 0, []

        # Check in standard lexicon first
        clean_text = text.strip()
        if clean_text in STANDARD_PITCH_LEXICON:
            pattern, kernel = STANDARD_PITCH_LEXICON[clean_text]
        elif hiragana in STANDARD_PITCH_LEXICON:
            pattern, kernel = STANDARD_PITCH_LEXICON[hiragana]
        else:
            # Rule-based fallback for general phrases & sentences
            pattern, kernel = cls._estimate_pattern_by_rules(hiragana, mora_count)

        expected_levels = cls.generate_expected_levels(mora_count, kernel)
        return pattern, kernel, expected_levels

    @classmethod
    def _estimate_pattern_by_rules(cls, hiragana: str, mora_count: int) -> tuple[PitchAccentPattern, int]:
        """Heuristic Tokyo accent estimation for multi-mora words / phrases."""
        # 1-mora words default to Heiban or Odaka
        if mora_count <= 1:
            return PitchAccentPattern.HEIBAN, 0

        # Verbs ending in ます / ました typically have accent kernel on the mora before ます
        if hiragana.endswith("ました") or hiragana.endswith("ません"):
            return PitchAccentPattern.NAKADAKA, max(1, mora_count - 3)
        if hiragana.endswith("ます") or hiragana.endswith("たい"):
            return PitchAccentPattern.NAKADAKA, max(1, mora_count - 2)
        if hiragana.endswith("です"):
            return PitchAccentPattern.ATAMADAKA if mora_count <= 3 else PitchAccentPattern.HEIBAN, 0

        # Over 50% of Japanese words are Heiban (0)
        return PitchAccentPattern.HEIBAN, 0

    @staticmethod
    def generate_expected_levels(mora_count: int, kernel: int) -> list[str]:
        """
        Generates standard Tokyo pitch level sequence ('H' or 'L') for each mora.
        Rules:
        - Mora 1 and Mora 2 ALWAYS have different pitch in Tokyo dialect (except 1-mora words).
        - Kernel = 0 (Heiban): [L, H, H, H, ...]
        - Kernel = 1 (Atamadaka): [H, L, L, L, ...]
        - Kernel = k (Nakadaka/Odaka): [L, H, H, ...(at k)..., L, L]
        """
        if mora_count <= 0:
            return []
        if mora_count == 1:
            return ["H" if kernel == 1 else "L"]

        levels = ["L"] * mora_count

        if kernel == 0:
            # Heiban: L H H H H ...
            levels[0] = "L"
            for i in range(1, mora_count):
                levels[i] = "H"
        elif kernel == 1:
            # Atamadaka: H L L L L ...
            levels[0] = "H"
            for i in range(1, mora_count):
                levels[i] = "L"
        else:
            # Nakadaka (kernel k): L H ... H (at index k-1) then L L ...
            levels[0] = "L"
            for i in range(1, min(kernel, mora_count)):
                levels[i] = "H"
            for i in range(kernel, mora_count):
                levels[i] = "L"

        return levels
