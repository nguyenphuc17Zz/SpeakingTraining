"""
JapaneseSequenceAligner — SOTA Sequence Alignment with Japanese Phonological Similarity.

Applies Needleman-Wunsch Dynamic Programming alignment with a domain-specific
phonological similarity matrix (consonant group, vowel group, voicing pairs,
and common Japanese-learner acoustic substitutions) to robustly align target
moras against user-spoken moras, gracefully absorbing fillers, insertions,
and deletions without index shifting.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domains.pronunciation.contracts import MoraUnit


@dataclass
class AlignmentPair:
    """Represents an aligned pair of target mora and user-uttered mora."""

    target_mora: MoraUnit | None
    user_kana: str | None
    operation: str  # "match", "substitution", "insertion", "deletion"
    similarity: float  # [0.0, 1.0]


class JapaneseSequenceAligner:
    """Performs optimal Needleman-Wunsch alignment between target and user moras."""

    # Voicing pairs (dakuten / handakuten pairs)
    VOICING_PAIRS: set[tuple[str, str]] = {
        ("か", "が"), ("き", "ぎ"), ("く", "ぐ"), ("け", "げ"), ("こ", "ご"),
        ("さ", "ざ"), ("し", "じ"), ("す", "ず"), ("せ", "ぜ"), ("そ", "ぞ"),
        ("た", "だ"), ("ち", "ぢ"), ("つ", "づ"), ("て", "で"), ("と", "ど"),
        ("は", "ば"), ("ひ", "び"), ("ふ", "ぶ"), ("へ", "べ"), ("ほ", "ぼ"),
        ("は", "ぱ"), ("ひ", "ぴ"), ("ふ", "ぷ"), ("へ", "ぺ"), ("ほ", "ぽ"),
    }

    # Common learner phonological substitutions
    LEARNER_SUBSTITUTIONS: set[tuple[str, str]] = {
        ("つ", "す"), ("つ", "ち"), ("つ", "と"),
        ("し", "ち"), ("じ", "ぢ"),
        ("ら", "だ"), ("り", "でぃ"), ("る", "どぅ"),
        ("ふ", "ほ"), ("ふ", "ふぅ"),
        ("お", "を"), ("え", "へ"),
    }

    # Consonant row groupings
    CONSONANT_GROUPS: list[set[str]] = [
        {"あ", "い", "う", "え", "お"},
        {"か", "き", "く", "け", "こ", "が", "ぎ", "ぐ", "げ", "ご"},
        {"さ", "し", "す", "せ", "そ", "ざ", "じ", "ず", "ぜ", "ぞ"},
        {"た", "ち", "つ", "て", "と", "だ", "ぢ", "づ", "で", "ど"},
        {"な", "に", "ぬ", "ね", "の"},
        {"は", "ひ", "ふ", "へ", "ほ", "ば", "び", "ぶ", "べ", "ぼ", "ぱ", "ぴ", "ぷ", "ぺ", "ぽ"},
        {"ま", "み", "む", "め", "も"},
        {"や", "ゆ", "よ"},
        {"ら", "り", "る", "れ", "ろ"},
        {"わ", "を", "ん"},
    ]

    # Vowel column groupings (Dan)
    VOWEL_GROUPS: list[set[str]] = [
        {"あ", "か", "さ", "た", "な", "は", "ま", "や", "ら", "わ", "が", "ざ", "だ", "ば", "ぱ"},
        {"い", "き", "し", "ち", "に", "ひ", "み", "り", "ぎ", "じ", "ぢ", "び", "ぴ"},
        {"う", "く", "す", "つ", "ぬ", "ふ", "む", "ゆ", "る", "ぐ", "ず", "づ", "ぶ", "ぷ"},
        {"え", "け", "せ", "て", "ね", "へ", "め", "れ", "げ", "ぜ", "で", "べ", "ぺ"},
        {"お", "こ", "そ", "と", "の", "ほ", "も", "よ", "ろ", "を", "ご", "ぞ", "ど", "ぼ", "ぽ"},
    ]

    MATCH_SCORE: float = 3.0
    VOICING_SCORE: float = 1.8
    SUBSTITUTION_SCORE: float = 1.2
    SAME_CONSONANT_SCORE: float = 0.8
    SAME_VOWEL_SCORE: float = 0.4
    MISMATCH_PENALTY: float = -1.5

    GAP_DELETION_PENALTY: float = -2.0
    GAP_INSERTION_PENALTY: float = -1.2  # Slightly lighter penalty for fillers/interjections

    @classmethod
    def similarity_score(cls, k1: str, k2: str) -> tuple[float, float]:
        """
        Returns (raw_dp_score, normalized_similarity [0.0, 1.0]).
        """
        if k1 == k2:
            return cls.MATCH_SCORE, 1.0

        pair = (k1, k2)
        rev = (k2, k1)

        if pair in cls.VOICING_PAIRS or rev in cls.VOICING_PAIRS:
            return cls.VOICING_SCORE, 0.75

        if pair in cls.LEARNER_SUBSTITUTIONS or rev in cls.LEARNER_SUBSTITUTIONS:
            return cls.SUBSTITUTION_SCORE, 0.65

        # Check same consonant group
        for group in cls.CONSONANT_GROUPS:
            if k1 in group and k2 in group:
                return cls.SAME_CONSONANT_SCORE, 0.50

        # Check same vowel group
        for group in cls.VOWEL_GROUPS:
            if k1 in group and k2 in group:
                return cls.SAME_VOWEL_SCORE, 0.35

        return cls.MISMATCH_PENALTY, 0.10

    @classmethod
    def align(
        cls,
        target_moras: list[MoraUnit],
        user_kana_list: list[str],
    ) -> list[AlignmentPair]:
        """
        Runs global Needleman-Wunsch alignment with Japanese phonetic scoring.
        Returns a list of AlignmentPair preserving all target_moras and capturing insertions.
        """
        n = len(target_moras)
        m = len(user_kana_list)

        if n == 0 and m == 0:
            return []

        if n == 0:
            return [
                AlignmentPair(
                    target_mora=None,
                    user_kana=k,
                    operation="insertion",
                    similarity=0.0,
                )
                for k in user_kana_list
            ]

        if m == 0:
            return [
                AlignmentPair(
                    target_mora=tm,
                    user_kana=None,
                    operation="deletion",
                    similarity=0.0,
                )
                for tm in target_moras
            ]

        # 1. Initialize DP matrix and traceback matrix
        # dp[i][j]: best alignment score of target[0..i-1] and user[0..j-1]
        dp = [[0.0] * (m + 1) for _ in range(n + 1)]
        traceback = [[0] * (m + 1) for _ in range(n + 1)]
        # 1: Diagonal (match/sub), 2: Up (deletion of target), 3: Left (insertion of user)

        for i in range(1, n + 1):
            dp[i][0] = dp[i - 1][0] + cls.GAP_DELETION_PENALTY
            traceback[i][0] = 2

        for j in range(1, m + 1):
            dp[0][j] = dp[0][j - 1] + cls.GAP_INSERTION_PENALTY
            traceback[0][j] = 3

        # 2. Fill DP table
        for i in range(1, n + 1):
            tm = target_moras[i - 1]
            for j in range(1, m + 1):
                uk = user_kana_list[j - 1]
                match_val, _ = cls.similarity_score(tm.kana, uk)

                score_diag = dp[i - 1][j - 1] + match_val
                score_del = dp[i - 1][j] + cls.GAP_DELETION_PENALTY
                score_ins = dp[i][j - 1] + cls.GAP_INSERTION_PENALTY

                best_score = max(score_diag, score_del, score_ins)
                dp[i][j] = best_score

                if best_score == score_diag:
                    traceback[i][j] = 1
                elif best_score == score_del:
                    traceback[i][j] = 2
                else:
                    traceback[i][j] = 3

        # 3. Traceback from (n, m) to (0, 0)
        curr_i = n
        curr_j = m
        aligned_pairs: list[AlignmentPair] = []

        while curr_i > 0 or curr_j > 0:
            move = traceback[curr_i][curr_j]

            if move == 1 or (curr_i > 0 and curr_j > 0 and move == 0):
                # Diagonal: match or substitution
                tm = target_moras[curr_i - 1]
                uk = user_kana_list[curr_j - 1]
                _, sim = cls.similarity_score(tm.kana, uk)
                op = "match" if tm.kana == uk else "substitution"
                aligned_pairs.append(
                    AlignmentPair(
                        target_mora=tm,
                        user_kana=uk,
                        operation=op,
                        similarity=sim,
                    )
                )
                curr_i -= 1
                curr_j -= 1
            elif move == 2 or curr_j == 0:
                # Up: deletion of target mora (user didn't pronounce it)
                tm = target_moras[curr_i - 1]
                aligned_pairs.append(
                    AlignmentPair(
                        target_mora=tm,
                        user_kana=None,
                        operation="deletion",
                        similarity=0.0,
                    )
                )
                curr_i -= 1
            else:
                # Left: insertion of user mora (extra sound / filler)
                uk = user_kana_list[curr_j - 1]
                aligned_pairs.append(
                    AlignmentPair(
                        target_mora=None,
                        user_kana=uk,
                        operation="insertion",
                        similarity=0.0,
                    )
                )
                curr_j -= 1

        aligned_pairs.reverse()
        return aligned_pairs
