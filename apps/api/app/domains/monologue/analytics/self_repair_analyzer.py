"""SelfRepairAnalyzer §22."""

from __future__ import annotations

import re

from app.domains.monologue.contracts import SelfRepairEvent


class SelfRepairAnalyzer:
    """
    SOTA Willem Levelt (1983) Tripartite Speech Self-Repair Alignment Engine.
    Deconstructs speech self-repair into [Reparandum] -> [Interregnum] -> [Reparans].
    Distinguishes active metalinguistic monitoring from disruptive speech breakdowns.
    """

    # Editing terms and interregnum indicators
    INTERREGNUM_CUES = [
        (re.compile(r"(正確に言うと|正確には|厳密に言うと|訂正します|言い直すと)"), "appropriateness_repair"),
        (re.compile(r"(ではなくて|ではなく|じゃなくて|じゃなく)"), "reformulation"),
        (re.compile(r"(というか|と言いますか|ていうか)"), "appropriateness_repair"),
        (re.compile(r"(いや[、,\s]|あ[、,\s]|違った|あ、すみません|ごめんなさい)"), "error_repair"),
        (re.compile(r"(えっと[、,\s].*ではなく)"), "reformulation"),
    ]

    # Pattern for abandoned clause: ends with conjunctive particle without continuation
    ABANDONED_RE = re.compile(r"(が|けど|ので|のに|から|けれど)[、\s]*$")

    def analyze(self, transcript: str, words: list[dict] | None = None) -> tuple[list[SelfRepairEvent], dict]:
        events: list[SelfRepairEvent] = []
        sentences = [s.strip() for s in re.split(r"[。！？\n]+", transcript) if s.strip()]

        for s in sentences:
            # 1. Levelt Interregnum Cue Matching & Tripartite Boundary Segmentation
            matched_cue = False
            for pat, typ in self.INTERREGNUM_CUES:
                m = pat.search(s)
                if m:
                    matched_cue = True
                    start, end = m.span()
                    reparandum = s[:start].strip()
                    reparans = s[end:].strip()
                    fragment = s[:80]

                    # Distinguish restart vs error repair based on reparandum presence
                    if not reparandum or len(reparandum) <= 2:
                        actual_type = "restart"
                    else:
                        actual_type = typ

                    events.append(SelfRepairEvent(
                        type=actual_type,
                        fragment=fragment,
                        success=len(reparans) > 0,
                    ))
                    break

            # 2. Check Abandoned Clause (syntactic breakdown)
            if not matched_cue and self.ABANDONED_RE.search(s):
                events.append(SelfRepairEvent(
                    type="abandoned_clause",
                    fragment=s[:80],
                    success=False,
                ))

            # 3. Hesitation Ellipsis (X……Y)
            if not matched_cue and ("……" in s or "…" in s):
                parts = [p.strip() for p in re.split(r"[…。]+", s) if p.strip()]
                if len(parts) >= 2:
                    events.append(SelfRepairEvent(
                        type="reformulation",
                        fragment=s[:80],
                        success=True,
                    ))

        # 4. Word-Level Lexical Substitution Alignment (when timestamps/tokens provided)
        if words and len(words) >= 3:
            for i in range(len(words) - 1):
                w_prev = words[i].get("word", "").strip()
                w_curr = words[i + 1].get("word", "").strip()
                # Check immediate lexical substitution (e.g. 行きます -> 行きました, 昨日 -> 今日)
                if w_prev and w_curr and w_prev != w_curr:
                    # Common stem check or prefix overlap (e.g. 2+ common chars)
                    common_prefix_len = 0
                    min_len = min(len(w_prev), len(w_curr))
                    while common_prefix_len < min_len and w_prev[common_prefix_len] == w_curr[common_prefix_len]:
                        common_prefix_len += 1
                    if common_prefix_len >= 2 and min_len >= 3:
                        frag = f"{w_prev} -> {w_curr}"
                        if not any(frag in e.fragment for e in events):
                            events.append(SelfRepairEvent(
                                type="error_repair",
                                fragment=frag,
                                success=True,
                            ))

        abandoned = sum(1 for e in events if e.type == "abandoned_clause")
        success = sum(1 for e in events if e.success)
        total = len(events)
        abandoned_rate = round(abandoned / max(1, total), 3) if total else 0.0
        efficiency_ratio = round(success / max(1, total), 3) if total else 1.0

        # Metalinguistic monitoring evaluation
        if total == 0:
            monitoring_quality = "uninterrupted_flow"
        elif abandoned_rate >= 0.40:
            monitoring_quality = "frequent_breakdowns"
        elif efficiency_ratio >= 0.70:
            monitoring_quality = "active_monitoring"
        else:
            monitoring_quality = "tentative_monitoring"

        summary = {
            "repair_count": total,
            "abandoned_count": abandoned,
            "success_count": success,
            "abandoned_rate": abandoned_rate,
            "repair_efficiency_ratio": efficiency_ratio,
            "monitoring_quality": monitoring_quality,
            "repair_frequency_per_min": None,
        }
        return events, summary
