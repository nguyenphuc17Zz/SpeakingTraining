from app.domains.pronunciation.contracts import PronunciationAnalysisPolicy


class PronunciationSamplingPolicy:
    """Decides whether and how deeply to analyze audio turns for pronunciation based on session mode and turn index."""

    @classmethod
    def determine_policy(
        cls,
        session_mode: str,
        turn_sequence: int = 1,
        is_dedicated_practice: bool = False,
    ) -> PronunciationAnalysisPolicy:
        """
        Returns policy level:
        - OFF: skip analysis
        - BASIC: phoneme, mora, and basic prosody
        - DEEP: full deep pitch extraction, DTW alignment, and multi-component assessment
        """
        if is_dedicated_practice:
            return PronunciationAnalysisPolicy.DEEP

        mode_lower = session_mode.lower() if session_mode else "conversation"

        if mode_lower in {"pronunciation", "practice", "shadowing"}:
            return PronunciationAnalysisPolicy.DEEP

        if mode_lower in {"coaching", "lesson", "tutor"}:
            return PronunciationAnalysisPolicy.BASIC

        # Standard Conversation mode: sample every 2nd or 3rd user turn to conserve CPU/GPU
        if mode_lower in {"conversation", "roleplay", "free_talk"}:
            if turn_sequence % 2 == 1:
                return PronunciationAnalysisPolicy.BASIC
            return PronunciationAnalysisPolicy.OFF

        return PronunciationAnalysisPolicy.BASIC
