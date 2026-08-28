class ScoreInterpreter:
    """Interprets 0-100 scores into standard pedagogical performance tiers."""

    @staticmethod
    def interpret(score: float) -> str:
        """Maps score to human tier."""
        if score >= 90.0:
            return "Excellent"
        if score >= 80.0:
            return "Very Good"
        if score >= 70.0:
            return "Good"
        if score >= 60.0:
            return "Developing"
        return "Needs Attention"

    @staticmethod
    def get_tier_color(score: float) -> str:
        """Returns standard Tailwind color identifier for score."""
        if score >= 90.0:
            return "emerald"
        if score >= 80.0:
            return "green"
        if score >= 70.0:
            return "blue"
        if score >= 60.0:
            return "amber"
        return "rose"
