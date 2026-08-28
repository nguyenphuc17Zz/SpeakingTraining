from app.domains.learner_memory.contracts import LearnerLevel, LevelConfidence


class LevelAssessor:
    """Evaluates cross-session performance metrics and calculates coarse speaking levels and confidence."""

    @classmethod
    def assess_levels(
        cls,
        total_sessions: int,
        total_turns: int,
        avg_session_score: float,
        must_fix_rate: float,       # must_fix corrections per turn
        total_corrections_rate: float, # total corrections per turn
        avg_response_speed_ms: float | None = None,
        weaknesses_count: int = 0,
        strengths_count: int = 0,
    ) -> dict[str, str | float]:
        """
        Calculates speaking, grammar, vocabulary, fluency, and overall levels.
        """
        # 1. Determine Level Confidence
        if total_sessions < 3 or total_turns < 10:
            level_conf = LevelConfidence.INSUFFICIENT_EVIDENCE
            conf_score = 0.35
        elif total_sessions < 6:
            level_conf = LevelConfidence.LOW
            conf_score = 0.55
        elif total_sessions < 15:
            level_conf = LevelConfidence.MEDIUM
            conf_score = 0.75
        else:
            level_conf = LevelConfidence.HIGH
            conf_score = 0.90

        # 2. Grammar Level
        # High must_fix_rate indicates basic structural confusion
        if must_fix_rate > 0.8:
            grammar_lvl = LearnerLevel.BEGINNER
        elif must_fix_rate > 0.4:
            grammar_lvl = LearnerLevel.ELEMENTARY
        elif must_fix_rate > 0.15:
            grammar_lvl = LearnerLevel.INTERMEDIATE
        elif must_fix_rate > 0.05:
            grammar_lvl = LearnerLevel.UPPER_INTERMEDIATE
        else:
            grammar_lvl = LearnerLevel.ADVANCED

        # 3. Fluency & Speed Level
        if avg_response_speed_ms and avg_response_speed_ms < 1500 and total_corrections_rate < 0.3:
            fluency_lvl = LearnerLevel.UPPER_INTERMEDIATE
        elif avg_response_speed_ms and avg_response_speed_ms > 4000:
            fluency_lvl = LearnerLevel.BEGINNER
        elif total_corrections_rate > 0.6:
            fluency_lvl = LearnerLevel.ELEMENTARY
        else:
            fluency_lvl = LearnerLevel.INTERMEDIATE

        # 4. Vocabulary Level
        if weaknesses_count > strengths_count * 2:
            vocab_lvl = LearnerLevel.ELEMENTARY
        elif strengths_count >= 3:
            vocab_lvl = LearnerLevel.UPPER_INTERMEDIATE
        else:
            vocab_lvl = LearnerLevel.INTERMEDIATE

        # 5. Naturalness Level
        if avg_session_score >= 88:
            naturalness_lvl = LearnerLevel.UPPER_INTERMEDIATE
        elif avg_session_score >= 75:
            naturalness_lvl = LearnerLevel.INTERMEDIATE
        elif avg_session_score >= 60:
            naturalness_lvl = LearnerLevel.ELEMENTARY
        else:
            naturalness_lvl = LearnerLevel.BEGINNER

        # 6. Overall & Speaking Level (Composite)
        score_points = {
            LearnerLevel.BEGINNER: 1,
            LearnerLevel.ELEMENTARY: 2,
            LearnerLevel.INTERMEDIATE: 3,
            LearnerLevel.UPPER_INTERMEDIATE: 4,
            LearnerLevel.ADVANCED: 5,
        }
        avg_points = (
            score_points[grammar_lvl]
            + score_points[fluency_lvl]
            + score_points[vocab_lvl]
            + score_points[naturalness_lvl]
        ) / 4.0

        if avg_points < 1.5:
            overall_lvl = LearnerLevel.BEGINNER
        elif avg_points < 2.5:
            overall_lvl = LearnerLevel.ELEMENTARY
        elif avg_points < 3.5:
            overall_lvl = LearnerLevel.INTERMEDIATE
        elif avg_points < 4.5:
            overall_lvl = LearnerLevel.UPPER_INTERMEDIATE
        else:
            overall_lvl = LearnerLevel.ADVANCED

        return {
            "overall_level": overall_lvl.value,
            "speaking_level": overall_lvl.value,
            "fluency_level": fluency_lvl.value,
            "grammar_level": grammar_lvl.value,
            "vocabulary_level": vocab_lvl.value,
            "naturalness_level": naturalness_lvl.value,
            "level_confidence": level_conf.value,
            "confidence_score": conf_score,
        }
