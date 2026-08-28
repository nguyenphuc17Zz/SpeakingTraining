"""FillerAnalyzer §20/21 — distinguishes filler vs discourse marker."""

from __future__ import annotations

import re

from app.domains.monologue.contracts import FillerEvent, TokenClass

# Small lexical resource for known fillers (not full inventory — AI fallback covers rest)
KNOWN_FILLERS = {"えーと", "えっと", "あのー", "あの", "そのー", "まあ", "なんというか", "ええと", "うーん", "あー"}
KNOWN_DISCOURSE = {"まず", "次に", "例えば", "つまり", "したがって", "そのため", "一方で", "しかし", "それで", "ところで", "実は"}
KNOWN_BACKCHANNEL = {"うん", "はい", "ええ", "そうですね"}

# Regex fallback for prolonged vowels
FILLER_RE = re.compile(r"^(えー+と|あのー+|そのー+|まあー*|えっと)$")


class FillerAnalyzer:
    def __init__(self):
        try:
            from app.domains.japanese.provider import get_language_provider

            self.lang = get_language_provider()
        except Exception:
            self.lang = None

    def classify_token(self, token: str) -> TokenClass:
        t = token.strip()
        if t in KNOWN_FILLERS or FILLER_RE.match(t):
            return TokenClass.FILLER
        if t in KNOWN_DISCOURSE:
            return TokenClass.DISCOURSE_MARKER
        if t in KNOWN_BACKCHANNEL:
            return TokenClass.BACKCHANNEL
        # heuristic: single kana prolonged
        if re.match(r"^[あ-んー]{1,3}$", t) and len(t) <= 2 and t in {"え", "あ", "ま"}:
            return TokenClass.FILLER
        return TokenClass.CONTENT_WORD

    def analyze(self, transcript: str, words: list[dict] | None = None) -> tuple[list[FillerEvent], dict]:
        events: list[FillerEvent] = []
        # Tokenize via language provider or regex (JP has no spaces)
        tokens: list[str] = []
        if self.lang:
            try:
                toks = self.lang.analyze(transcript)
                tokens = [t.surface for t in toks]
            except Exception as e:
                from app.core.logging import logger
                logger.debug(f"[FillerAnalyzer] analyze fallback: {e}")
                tokens = re.findall(r"[ぁ-んァ-ン一-龯a-zA-Z0-9_]+|[^\s]", transcript)
        else:
            tokens = re.findall(r"[ぁ-んァ-ン一-龯a-zA-Z0-9_]+|[^\s]", transcript)

        # Map words timestamps if available
        word_map = {w.get("word", "").strip(): w for w in (words or [])}

        for tok in tokens:
            cls = self.classify_token(tok)
            if cls == TokenClass.FILLER:
                w = word_map.get(tok, {})
                events.append(FillerEvent(token=tok, start_ms=w.get("start_ms"), end_ms=w.get("end_ms"), token_class=cls))
            elif cls == TokenClass.SELF_REPAIR:
                # handled elsewhere
                pass

        # Substring fallback for fillers missed by tokenizer (e.g., with punctuation) — deduplicated
        for filler in KNOWN_FILLERS:
            if filler in transcript:
                cnt_transcript = transcript.count(filler)
                cnt_already = sum(1 for e in events if e.token == filler)
                to_add = cnt_transcript - cnt_already
                for _ in range(max(0, to_add)):
                    events.append(FillerEvent(token=filler, token_class=TokenClass.FILLER))

        total_tokens = max(1, len(tokens))
        duration_min = 1  # will be overwritten by caller; compute per_min lazily
        # caller will compute filler_per_min from duration
        filler_ratio = round(len(events) / total_tokens, 3) if total_tokens else 0

        # filler clusters: consecutive fillers within 2 tokens
        clusters = 0
        for i in range(1, len(events)):
            if events[i].start_ms and events[i - 1].end_ms and events[i].start_ms - events[i - 1].end_ms < 2000:
                clusters += 1

        summary = {
            "filler_count": len(events),
            "filler_ratio": filler_ratio,
            "clusters": clusters,
            "total_tokens": total_tokens,
        }
        return events, summary

    @staticmethod
    def fillers_per_minute(filler_count: int, duration_ms: int) -> float:
        mins = max(0.2, duration_ms / 60000)
        return round(filler_count / mins, 2)
