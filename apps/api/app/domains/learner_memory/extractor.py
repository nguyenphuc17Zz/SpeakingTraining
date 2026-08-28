from typing import Any

from app.domains.conversation_intelligence.models import (
    AnalysisCorrection,
    GrammarNote,
    SessionAnalysis,
    TurnAnalysis,
    VocabularyNote,
)
from app.domains.learner_memory.contracts import MemoryCandidate, MemoryType
from app.domains.learner_memory.key_resolver import MemoryKeyResolver


class MemoryExtractor:
    """Extracts typed learning signal candidates from turn-level analyses and whole-session analyses."""

    # Policy weights
    WEIGHT_MUST_FIX = 1.0
    WEIGHT_SHOULD_FIX = 0.6
    WEIGHT_NATIVE_ALT = 0.3
    WEIGHT_SESSION_PATTERN = 1.2
    WEIGHT_STRENGTH = 0.8
    WEIGHT_CORRECT_USAGE = 0.7

    @classmethod
    def extract_from_turn_analysis(
        cls,
        turn_analysis: TurnAnalysis,
        context_tag: str | None = None,
    ) -> list[MemoryCandidate]:
        """Extracts candidates from a single turn analysis."""
        candidates: list[MemoryCandidate] = []

        # 1. Skip if transcript was marked suspicious and no high-confidence corrections exist
        if turn_analysis.is_suspicious_transcript:
            high_conf = [c for c in turn_analysis.corrections if c.confidence == "high" and c.severity == "MUST_FIX"]
            if not high_conf:
                return candidates

        # 2. Extract corrections
        for corr in turn_analysis.corrections:
            if corr.severity == "IGNORE":
                continue

            # Resolve canonical key
            m_type, key, default_stmt = MemoryKeyResolver.resolve_key(
                category=corr.category,
                identifier_hint=corr.corrected or corr.category,
                original_snippet=corr.original,
            )

            # Assign weight
            weight = cls.WEIGHT_SHOULD_FIX
            if corr.severity == "MUST_FIX":
                weight = cls.WEIGHT_MUST_FIX
            elif corr.severity == "NATIVE_ALTERNATIVE":
                weight = cls.WEIGHT_NATIVE_ALT

            conf_val = 0.9 if corr.confidence == "high" else (0.65 if corr.confidence == "medium" else 0.4)

            statement = corr.explanation or default_stmt

            candidate = MemoryCandidate(
                memory_type=m_type,
                key=key,
                statement=statement,
                category=corr.category,
                severity=corr.severity,
                severity_score=corr.severity_score,
                confidence=conf_val,
                evidence_weight=weight,
                evidence_type="error_observation",
                original_snippet=corr.original,
                corrected_snippet=corr.corrected,
                context_tag=context_tag,
                session_id=turn_analysis.session_id,
                turn_id=turn_analysis.turn_id,
                turn_analysis_id=turn_analysis.id,
                correction_id=corr.id,
                metadata={
                    "native_alternative": corr.native_alternative,
                    "acceptable_alternatives": corr.acceptable_alternatives,
                },
            )
            candidates.append(candidate)

        # 3. Extract grammar notes (both correct usage and errors)
        for gn in turn_analysis.grammar_notes:
            m_type, key, default_stmt = MemoryKeyResolver.resolve_key(
                category="grammar",
                identifier_hint=gn.grammar_pattern,
                original_snippet=gn.user_usage,
            )
            # If user usage was essentially correct, record positive attempt
            is_correct = gn.user_usage.strip() == gn.correct_usage.strip()
            ev_type = "correct_observation" if is_correct else "error_observation"
            ev_weight = cls.WEIGHT_CORRECT_USAGE if is_correct else cls.WEIGHT_SHOULD_FIX

            candidate = MemoryCandidate(
                memory_type=m_type,
                key=key,
                statement=gn.short_explanation or default_stmt,
                category="grammar",
                severity="STRENGTH" if is_correct else "SHOULD_FIX",
                severity_score=30 if is_correct else 60,
                confidence=0.85,
                evidence_weight=ev_weight,
                evidence_type=ev_type,
                original_snippet=gn.user_usage,
                corrected_snippet=gn.correct_usage,
                context_tag=context_tag,
                session_id=turn_analysis.session_id,
                turn_id=turn_analysis.turn_id,
                turn_analysis_id=turn_analysis.id,
                metadata={"example_sentence": gn.example_sentence},
            )
            candidates.append(candidate)

        # 4. Extract turn-level strengths
        if turn_analysis.strengths:
            for s_text in turn_analysis.strengths:
                if len(s_text.strip()) < 4:
                    continue
                m_type, key, default_stmt = MemoryKeyResolver.resolve_key(
                    category="strength",
                    identifier_hint=s_text,
                )
                candidate = MemoryCandidate(
                    memory_type=MemoryType.STRENGTH,
                    key=key,
                    statement=s_text,
                    category="speaking_strength",
                    severity="STRENGTH",
                    severity_score=20,
                    confidence=0.8,
                    evidence_weight=cls.WEIGHT_STRENGTH,
                    evidence_type="turn_strength",
                    session_id=turn_analysis.session_id,
                    turn_id=turn_analysis.turn_id,
                    turn_analysis_id=turn_analysis.id,
                    context_tag=context_tag,
                )
                candidates.append(candidate)

        return candidates

    @classmethod
    def extract_from_session_analysis(
        cls,
        session_analysis: SessionAnalysis,
        context_tag: str | None = None,
    ) -> list[MemoryCandidate]:
        """Extracts repeated issue signals and holistic strengths from session analysis."""
        candidates: list[MemoryCandidate] = []

        # 1. Repeated issues detected across the session
        if session_analysis.repeated_issues:
            for ri in session_analysis.repeated_issues:
                pattern = ri.get("pattern") or ri.get("issue") or ri.get("category") or "repeated_pattern"
                explanation = ri.get("explanation") or ri.get("description") or f"Lỗi lặp lại trong phiên: {pattern}"
                count = int(ri.get("count", 2))

                m_type, key, default_stmt = MemoryKeyResolver.resolve_key(
                    category=ri.get("category", "grammar"),
                    identifier_hint=pattern,
                )

                candidate = MemoryCandidate(
                    memory_type=m_type,
                    key=key,
                    statement=explanation or default_stmt,
                    category=ri.get("category", "repeated_pattern"),
                    severity="MUST_FIX" if count >= 3 else "SHOULD_FIX",
                    severity_score=75,
                    confidence=0.92,
                    evidence_weight=cls.WEIGHT_SESSION_PATTERN * min(2.0, count * 0.5),
                    evidence_type="session_repeated_pattern",
                    session_id=session_analysis.session_id,
                    context_tag=context_tag,
                    metadata={"occurrences_in_session": count, "pattern": pattern},
                )
                candidates.append(candidate)

        # 2. Session-level strengths
        if session_analysis.strengths:
            for st in session_analysis.strengths:
                if len(st.strip()) < 4:
                    continue
                m_type, key, default_stmt = MemoryKeyResolver.resolve_key(
                    category="strength",
                    identifier_hint=st,
                )
                candidate = MemoryCandidate(
                    memory_type=MemoryType.STRENGTH,
                    key=key,
                    statement=st,
                    category="session_strength",
                    severity="STRENGTH",
                    severity_score=20,
                    confidence=0.88,
                    evidence_weight=cls.WEIGHT_STRENGTH * 1.2,
                    evidence_type="session_strength",
                    session_id=session_analysis.session_id,
                    context_tag=context_tag,
                )
                candidates.append(candidate)

        return candidates
