"""SelfRepairAnalyzer §22."""

from __future__ import annotations

import re

from app.domains.monologue.contracts import SelfRepairEvent


class SelfRepairAnalyzer:
    # cue phrases indicating self-repair in Japanese monologue (small lexical resource)
    REPAIR_CUES = [
        r"正確に言うと",
        r"いや、",
        r"すみません、",
        r"訂正します",
        r"ではなく",
        r"ではなくて",
        r"と言いますか",
        r"というか",
        r"あ、",
        r"えっと、.*ではなく",
    ]
    # Pattern for abandoned clause: ends with が/けど without continuation
    ABANDONED_RE = re.compile(r"(が|けど|ので|のに)[、\s]*$")

    def analyze(self, transcript: str, words: list[dict] | None = None) -> tuple[list[SelfRepairEvent], dict]:
        events: list[SelfRepairEvent] = []
        # Split into sentences
        sentences = re.split(r"[。！？\n]+", transcript)
        for sent in sentences:
            s = sent.strip()
            if not s:
                continue
            # Check repair cues
            for pat in self.REPAIR_CUES:
                if re.search(pat, s):
                    # Determine type
                    if "正確に言うと" in s or "訂正" in s:
                        typ = "correction"
                    elif "ではなく" in s:
                        typ = "reformulation"
                    elif re.search(r"いや、|あ、|すみません", s):
                        typ = "restart"
                    else:
                        typ = "clarification"
                    events.append(SelfRepairEvent(type=typ, fragment=s[:80], success=True))
                    break
            # Check abandoned
            if self.ABANDONED_RE.search(s):
                events.append(SelfRepairEvent(type="abandoned_clause", fragment=s[:80], success=False))

        # Heuristic: repeated phrase with correction (X……Y)
        if "……" in transcript or "…" in transcript:
            parts = re.split(r"[…。]+", transcript)
            if len(parts) >= 2:
                # if last part contains cue → already counted, else add generic reformulation
                pass

        abandoned = sum(1 for e in events if e.type == "abandoned_clause")
        success = sum(1 for e in events if e.success)
        total = len(events)
        abandoned_rate = round(abandoned / max(1, total), 3) if total else 0.0
        summary = {
            "repair_count": total,
            "abandoned_count": abandoned,
            "success_count": success,
            "abandoned_rate": abandoned_rate,
            "repair_frequency_per_min": None,  # caller fills with duration
        }
        return events, summary
