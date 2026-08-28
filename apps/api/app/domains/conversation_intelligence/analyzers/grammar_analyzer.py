from app.domains.conversation_intelligence.contracts import GrammarPointNote


class GrammarAnalyzer:
    """Extracts and validates key grammar points and patterns from turn analysis."""

    @staticmethod
    def process_grammar_points(points: list[GrammarPointNote]) -> list[GrammarPointNote]:
        seen = set()
        unique_points = []
        for p in points:
            if p.grammar_pattern and p.grammar_pattern not in seen:
                seen.add(p.grammar_pattern)
                unique_points.append(p)
        return unique_points
