from app.domains.conversation_intelligence.contracts import VocabularyNote


class VocabularyAnalyzer:
    """Extracts vocabulary suggestions and detects repetitive word choices."""

    @staticmethod
    def process_vocabulary_notes(notes: list[VocabularyNote]) -> list[VocabularyNote]:
        # Filter out empty or duplicate notes
        seen = set()
        unique_notes = []
        for n in notes:
            if n.original_word and n.original_word not in seen:
                seen.add(n.original_word)
                unique_notes.append(n)
        return unique_notes
