"""ConversationRecoveryEngine — repair as skill."""

from __future__ import annotations


REPAIR_PHRASES = {
    "ask_repeat": ["もう一度お願いします", "すみません、よく聞こえませんでした", "もう一度言っていただけますか"],
    "confirm": ["確認させてください", "で合っていますか"],
    "clarify": ["すみません、どういう意味ですか"],
}


class ConversationRecoveryEngine:
    def detect_repair_need(self, transcript: str, intent_confidence: float, stt_confidence: float | None = None) -> dict:
        # If STT low confidence or intent UNKNOWN, suggest repair
        needs_repair = False
        reason = ""
        if stt_confidence is not None and stt_confidence < 0.6:
            needs_repair = True
            reason = "low_stt_confidence"
        elif intent_confidence < 0.5:
            needs_repair = True
            reason = "low_intent_confidence"
        # Check for repair phrases in transcript
        is_repair_attempt = any(phrase in transcript for phrases in REPAIR_PHRASES.values() for phrase in phrases)
        return {"needs_repair": needs_repair, "reason": reason, "is_repair_attempt": is_repair_attempt}

    def score_recovery(self, attempts: list[dict]) -> dict:
        # attempts: list of {is_repair_attempt, success}
        total = len([a for a in attempts if a.get("is_repair_attempt")])
        successes = len([a for a in attempts if a.get("is_repair_attempt") and a.get("success")])
        rate = successes / total if total else 1.0
        return {"recovery_attempts": total, "recovery_successes": successes, "recovery_rate": round(rate, 2)}
