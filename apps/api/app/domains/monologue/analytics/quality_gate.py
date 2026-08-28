"""SpeechQualityGate §16."""

from __future__ import annotations

from app.domains.monologue.contracts import SpeechQualityGateResult


class SpeechQualityGate:
    @staticmethod
    def evaluate(
        audio_bytes: bytes | None,
        speech_duration_ms: int | None,
        target_duration_ms: int,
        stt_confidence: float | None,
        word_count: int | None,
        has_clipping: bool = False,
        snr_db: float | None = None,
    ) -> SpeechQualityGateResult:
        if not audio_bytes or len(audio_bytes) == 0:
            return SpeechQualityGateResult(status="RETRY_AUDIO", reason="Audio too short/empty", has_voice=False)
        # Primary 0.5s check via duration_ms (per user choice); byte length only as fallback when duration unknown
        if speech_duration_ms is not None:
            if speech_duration_ms < 500:
                return SpeechQualityGateResult(status="RETRY_AUDIO", reason="Audio too short (<0.5s)", has_voice=False)
            if speech_duration_ms < 1500 and (word_count or 0) < 3:
                return SpeechQualityGateResult(status="RETRY_AUDIO", reason="Speech too short", stt_confidence=stt_confidence, has_voice=False)
        else:
            # fallback when duration unknown: ~0.5s at 16kHz 16-bit mono = 16000 bytes
            if len(audio_bytes) < 16000:
                return SpeechQualityGateResult(status="RETRY_AUDIO", reason="Audio too short/empty (<0.5s)", has_voice=False)
        if (word_count or 0) == 0:
            return SpeechQualityGateResult(status="RETRY_AUDIO", reason="No words detected (possible VAD failure)", stt_confidence=stt_confidence, has_voice=False)
        if stt_confidence is not None and stt_confidence < 0.35:
            return SpeechQualityGateResult(status="LOW_CONFIDENCE", reason="STT confidence very low", stt_confidence=stt_confidence)
        if has_clipping and (word_count or 0) < 5:
            return SpeechQualityGateResult(status="LOW_CONFIDENCE", reason="Clipping + few words", stt_confidence=stt_confidence, clipping=True)
        if snr_db is not None and snr_db < 5 and stt_confidence is not None and stt_confidence < 0.5:
            return SpeechQualityGateResult(status="LOW_CONFIDENCE", reason="Noisy background", stt_confidence=stt_confidence)
        return SpeechQualityGateResult(status="ok", stt_confidence=stt_confidence, has_voice=True, clipping=has_clipping)
