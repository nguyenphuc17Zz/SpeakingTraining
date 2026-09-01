"""ElaborationEngine — detects under-elaboration and builds progressive prompts.

§20 Controlled Elaboration, §21 Forced Elaboration, §22 Response Length Target.
"""

from __future__ import annotations

import re
from typing import Any

from app.core.logging import logger
from app.domains.ramp.contracts import (
    ElaborationPrompt,
    ElaborationSignal,
)


# Reason markers in Japanese
_REASON_MARKERS = [
    "から", "ので", "なぜなら", "というのは", "そのため", "だから",
    "のは", "理由は", "わけは",
]

# Example markers in Japanese
_EXAMPLE_MARKERS = [
    "例えば", "たとえば", "例として", "といえば", "など", "なんか",
    "ような", "たりします", "をはじめ",
]

# Sentence-ending particles / verb forms that signal a complete sentence
_SENTENCE_ENDERS = re.compile(r"[。！？]|ます[。]?|です[。]?|した[。]?|でした[。]?|ました[。]?$")


class ElaborationEngine:
    """
    Detects elaboration deficits and generates progressive cues.
    Deterministic — no AI calls. §21
    """

    def detect_signals(
        self,
        transcript: str,
        stage: int,
        measured_level: str,
        word_count_threshold: int | None = None,
    ) -> list[ElaborationSignal]:
        """Return list of detected elaboration issues."""
        signals: list[ElaborationSignal] = []
        text = transcript.strip()

        if not text:
            signals.append(ElaborationSignal.TOO_SHORT)
            return signals

        words = self._count_meaningful_tokens(text)
        threshold = word_count_threshold or self._get_threshold(stage, measured_level)

        # §76 Short answer detection
        if words < threshold:
            signals.append(ElaborationSignal.TOO_SHORT)

        # Check sentence completeness (§12 one-sentence response)
        if not self._is_complete_sentence(text):
            signals.append(ElaborationSignal.INCOMPLETE_SENTENCE)

        # §14 F — Answer + Reason checks (stages 5+)
        if stage >= 5 and not self._has_reason(text):
            signals.append(ElaborationSignal.NO_REASON)

        # §15 G — Answer + Example checks (stages 6+)
        if stage >= 6 and not self._has_example(text):
            signals.append(ElaborationSignal.NO_EXAMPLE)

        # Content-word only (e.g., "映画。")
        if self._is_content_word_only(text):
            signals.append(ElaborationSignal.CONTENT_WORD_ONLY)

        return signals

    def has_reason(self, transcript: str) -> bool:
        return self._has_reason(transcript)

    def has_example(self, transcript: str) -> bool:
        return self._has_example(transcript)

    def is_sentence_complete(self, transcript: str) -> bool:
        return self._is_complete_sentence(transcript)

    def build_elaboration_prompt(
        self,
        signals: list[ElaborationSignal],
        stage: int,
        step: int = 1,
    ) -> ElaborationPrompt | None:
        """
        Return progressive elaboration cue. §20
        step 1=detail, 2=reason, 3=example, 4=compare
        """
        if not signals:
            return None

        primary = signals[0]

        if primary == ElaborationSignal.INCOMPLETE_SENTENCE:
            return ElaborationPrompt(
                signal=primary,
                cue_jp="もう少し長い文で言ってみましょう。",
                cue_vi="Hãy nói thành một câu đầy đủ.",
                step=1,
            )

        if primary == ElaborationSignal.CONTENT_WORD_ONLY:
            return ElaborationPrompt(
                signal=primary,
                cue_jp="「〜ました」「〜です」などを使って、完全な文にしましょう。",
                cue_vi="Hãy dùng 「〜ました」「〜です」 để tạo thành câu đầy đủ.",
                step=1,
            )

        if primary == ElaborationSignal.TOO_SHORT:
            cues = {
                1: ("もう一つ詳細を追加してみてください。", "Hãy thêm một chi tiết."),
                2: ("なぜですか？理由を教えてください。", "Hãy giải thích lý do."),
                3: ("例えば、どんなことがありましたか？", "Ví dụ, điều gì đã xảy ra?"),
                4: ("〜と比べると、どうですか？", "So sánh với điều gì đó thì sao?"),
            }
            jp, vi = cues.get(step, cues[1])
            return ElaborationPrompt(signal=primary, cue_jp=jp, cue_vi=vi, step=step)

        if primary == ElaborationSignal.NO_REASON:
            return ElaborationPrompt(
                signal=primary,
                cue_jp="なぜですか？「〜から」「〜ので」を使って理由を言ってみましょう。",
                cue_vi="Tại sao? Hãy dùng 「〜から」「〜ので」 để giải thích lý do.",
                step=2,
            )

        if primary == ElaborationSignal.NO_EXAMPLE:
            return ElaborationPrompt(
                signal=primary,
                cue_jp="例えば、具体的な例を挙げてみてください。",
                cue_vi="Ví dụ, hãy đưa ra một ví dụ cụ thể.",
                step=3,
            )

        return None

    def build_retry_variation(
        self,
        original_prompt_jp: str,
        stage: int,
        attempt_number: int,
    ) -> str:
        """
        Return a close variation of the prompt for retry. §38
        Same skill, different surface form — avoids memorization.
        """
        # Simple time/context variation (deterministic, no AI)
        time_variations = [
            original_prompt_jp,
            original_prompt_jp.replace("週末", "昨日"),
            original_prompt_jp.replace("最近", "先週"),
            original_prompt_jp.replace("今日", "昨日"),
        ]
        idx = attempt_number % len(time_variations)
        varied = time_variations[idx]

        # Add elaboration nudge for retries
        if stage >= 3 and attempt_number > 0:
            varied += "（できるだけ詳しく話してください。）"

        return varied

    # ---------------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------------

    def _count_meaningful_tokens(self, text: str) -> int:
        """Rough word count for Japanese (by character block + punctuation split)."""
        # Remove punctuation
        clean = re.sub(r"[。、！？\s]", " ", text)
        # Count non-empty segments
        segments = [s for s in clean.split() if s]
        # Also count chars as proxy (Japanese doesn't space words)
        char_count = len(re.sub(r"[\s。、！？]", "", text))
        # Use max of segment count and char_count/3 (rough mora proxy)
        return max(len(segments), char_count // 3)

    def _get_threshold(self, stage: int, measured_level: str) -> int:
        """§21 stage-specific minimum word count."""
        base = {
            0: 2, 1: 3, 2: 5, 3: 6, 4: 10,
            5: 12, 6: 16, 7: 20, 8: 25, 9: 32, 10: 40,
        }
        t = base.get(stage, 10)
        if measured_level in ("N1", "N2"):
            t = int(t * 1.1)
        return t

    def _is_complete_sentence(self, text: str) -> bool:
        """Check if text ends with a sentence-final marker."""
        text_clean = text.strip()
        # Ends with Japanese sentence ender
        if _SENTENCE_ENDERS.search(text_clean):
            return True
        # Ends with punctuation
        if text_clean and text_clean[-1] in ("。", "！", "？", ".", "!", "?"):
            return True
        # At least has a verb-like ending (rough check)
        return bool(re.search(r"[うくすつぬふむゆるをんいきしちにひみりい]$", text_clean))

    def _has_reason(self, text: str) -> bool:
        return any(marker in text for marker in _REASON_MARKERS)

    def _has_example(self, text: str) -> bool:
        return any(marker in text for marker in _EXAMPLE_MARKERS)

    def _is_content_word_only(self, text: str) -> bool:
        """Detect single-word or single-noun answers (e.g., '映画。')."""
        clean = re.sub(r"[。！？、\s]", "", text.strip())
        # Rough: if clean text is very short and has no verb markers
        if len(clean) <= 6:
            has_verb = bool(re.search(r"[まですしたをにはがでもう]", clean))
            return not has_verb
        return False
