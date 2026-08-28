from app.domains.learner_memory.contracts import MemoryCandidate, MemoryType
from app.domains.pronunciation.contracts import (
    AnalysisConfidenceLevel,
    PronunciationResult,
)


class PronunciationLearningSignalExtractor:
    """Extracts persistent learning signal candidates from pronunciation analysis results for Phase 5 LearnerMemory."""

    @classmethod
    def extract_from_pronunciation_result(
        cls,
        result: PronunciationResult,
        user_id: str,
        session_id: str | None = None,
        turn_id: str | None = None,
        context_tag: str | None = "pronunciation_practice",
    ) -> list[MemoryCandidate]:
        """
        Transforms prioritized pronunciation issues and strengths into normalized MemoryCandidates.
        Does NOT store raw audio or pitch contours into learner memory.
        """
        candidates: list[MemoryCandidate] = []
        resolved_session_id = session_id or "pronunciation_session"

        # 1. Pronunciation Issues -> Weakness candidates
        for issue in result.top_issues:
            mem_type = MemoryType.PRONUNCIATION
            if "pitch_accent" in issue.issue_key:
                mem_type = MemoryType.PITCH_ACCENT
            elif "fluency" in issue.issue_key or "rhythm" in issue.issue_key:
                mem_type = MemoryType.FLUENCY

            conf_val = 0.85 if result.overall_confidence == AnalysisConfidenceLevel.HIGH else 0.60

            candidate = MemoryCandidate(
                memory_type=mem_type,
                key=issue.issue_key,
                statement=f"{issue.title}: {issue.explanation}",
                category=issue.category,
                severity=issue.severity,
                severity_score=75 if issue.severity == "MUST_FIX" else 55,
                confidence=conf_val,
                evidence_weight=1.0 if issue.severity == "MUST_FIX" else 0.65,
                evidence_type="error_observation",
                original_snippet=issue.detected_snippet,
                corrected_snippet=issue.target_snippet,
                context_tag=context_tag,
                session_id=resolved_session_id,
                turn_id=turn_id,
                metadata={
                    "practice_tip": issue.practice_tip,
                    "overall_score": result.overall_score,
                    "engine_version": result.engine_version,
                },
            )
            candidates.append(candidate)

        # 2. Pronunciation Strengths -> Strength candidates
        for strength_text in result.strengths:
            if len(strength_text.strip()) < 5:
                continue

            candidate = MemoryCandidate(
                memory_type=MemoryType.STRENGTH,
                key=f"strength.pronunciation.{abs(hash(strength_text)) % 10000}",
                statement=strength_text,
                category="pronunciation_strength",
                severity="STRENGTH",
                severity_score=25,
                confidence=0.88,
                evidence_weight=0.80,
                evidence_type="strength",
                context_tag=context_tag,
                session_id=resolved_session_id,
                turn_id=turn_id,
                metadata={
                    "overall_score": result.overall_score,
                },
            )
            candidates.append(candidate)

        return candidates
