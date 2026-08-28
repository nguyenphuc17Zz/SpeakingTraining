import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.ai.contracts import (
    AIMessage,
    AIMessageRole,
    AIRequest,
    AIResponse,
    AITask,
    ResponseFormat,
    ResponseFormatType,
)
from app.domains.ai.router import AIRouter
from app.domains.conversation_intelligence.analyzers.context_analyzer import ContextAnalyzer
from app.domains.conversation_intelligence.analyzers.correction_analyzer import CorrectionAnalyzer
from app.domains.conversation_intelligence.analyzers.feedback_prioritizer import FeedbackPrioritizer
from app.domains.conversation_intelligence.analyzers.grammar_analyzer import GrammarAnalyzer
from app.domains.conversation_intelligence.analyzers.naturalness_analyzer import NaturalnessAnalyzer
from app.domains.conversation_intelligence.analyzers.session_analyzer import SessionAnalyzer
from app.domains.conversation_intelligence.analyzers.vocabulary_analyzer import VocabularyAnalyzer
from app.domains.conversation_intelligence.contracts import (
    AnalysisConfidence,
    AnalysisPolicyConfig,
    ContextNote,
    ConversationAnalysisInput,
    CorrectionCategory,
    CorrectionItem,
    CorrectionSeverity,
    GrammarPointNote,
    SessionAnalysisResult,
    TurnAnalysisResult,
    VocabularyNote,
)
from app.domains.conversation_intelligence.prompts import (
    PROMPT_VERSION_SESSION_ANALYSIS,
    PROMPT_VERSION_TURN_ANALYSIS,
    SESSION_ANALYSIS_JSON_SCHEMA,
    SESSION_ANALYSIS_SYSTEM_PROMPT,
    TURN_ANALYSIS_JSON_SCHEMA,
    TURN_ANALYSIS_SYSTEM_PROMPT,
    PromptBuilder,
)


class AnalysisOrchestrator:
    """Master orchestrator for conversation turn and session deep analysis."""

    TRIVIAL_UTTERANCES = {"はい", "うん", "ええ", "そうですね", "なるほど", "わかりました", "こんにちは", "ありがとう", "どうも"}

    def __init__(self, db_session: AsyncSession, policy: AnalysisPolicyConfig | None = None):
        self.db_session = db_session
        self.ai_router = AIRouter(db_session)
        self.policy = policy or AnalysisPolicyConfig()

    @staticmethod
    def compute_input_hash(transcript: str, persona_role: str, mode: str) -> str:
        data = f"{transcript.strip().lower()}:{persona_role}:{mode}:{PROMPT_VERSION_TURN_ANALYSIS}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    async def analyze_turn(
        self,
        input_data: ConversationAnalysisInput,
        user_id: str | None = None,
    ) -> TurnAnalysisResult:
        """Executes multi-stage linguistic & correctness analysis for a single user turn."""
        clean_text = input_data.current_user_transcript.strip()
        is_suspicious = bool(input_data.stt_confidence is not None and input_data.stt_confidence < 0.6)

        # 1. Cost-aware Short Utterance Bypass
        if clean_text in self.TRIVIAL_UTTERANCES or len(clean_text) <= 2:
            return TurnAnalysisResult(
                turn_id=input_data.current_turn_id,
                session_id=input_data.session_id,
                overall_quality_score=95,
                communicative_success=True,
                strengths=["Phản xạ tự nhiên và tương tác tốt trong hội thoại."],
                corrections=[],
                grammar_points=[],
                vocabulary_notes=[],
                context_notes=[],
                priority_issues=[],
                is_suspicious_transcript=is_suspicious,
                prompt_version=PROMPT_VERSION_TURN_ANALYSIS,
                analyzer_version="1.0.0",
                analyzed_at=datetime.now(timezone.utc),
            )

        # 2. Build Structured AI Request
        user_msg = PromptBuilder.build_turn_analysis_user_message(input_data)
        ai_request = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=user_msg)],
            system_instruction=TURN_ANALYSIS_SYSTEM_PROMPT,
            task=AITask.CONVERSATION_ANALYSIS,
            temperature=0.2,
            response_format=ResponseFormat(
                type=ResponseFormatType.JSON_SCHEMA,
                json_schema=TURN_ANALYSIS_JSON_SCHEMA,
            ),
        )

        try:
            ai_response: AIResponse = await self.ai_router.generate(
                task=AITask.CONVERSATION_ANALYSIS,
                request=ai_request,
                user_id=user_id,
            )
            raw_data = self._parse_json_response(ai_response.text)
            provider_used = ai_response.provider
            model_used = ai_response.model
        except Exception as e:
            logger.warning(f"[AnalysisOrchestrator] AI generation failed or returned malformed JSON: {e}")
            raw_data = {}
            provider_used = "fallback"
            model_used = "fallback"

        # 3. Normalize & Parse Components
        quality_score = raw_data.get("overall_quality_score", 80)
        success = raw_data.get("communicative_success", True)
        strengths = raw_data.get("strengths", ["Phát âm và diễn đạt lưu loát."])
        if not strengths:
            strengths = ["Diễn đạt ý kiến tự tin và rõ ràng."]

        raw_corrections = raw_data.get("corrections", [])
        parsed_corrections: list[CorrectionItem] = []

        for c in raw_corrections:
            try:
                item = CorrectionItem(
                    category=CorrectionCategory(c.get("category", "grammar")),
                    severity=CorrectionSeverity(c.get("severity", "SHOULD_FIX")),
                    original=c.get("original", clean_text),
                    corrected=c.get("corrected", clean_text),
                    explanation=c.get("explanation", ""),
                    native_alternative=c.get("native_alternative"),
                    acceptable_alternatives=c.get("acceptable_alternatives", []),
                    context_note=c.get("context_note"),
                    confidence=AnalysisConfidence(c.get("confidence", "high")),
                    severity_score=c.get("severity_score", 50),
                )
                # Apply pedagogical guardrails
                sanitized = CorrectionAnalyzer.sanitize_correction(item, is_suspicious_transcript=is_suspicious)
                parsed_corrections.append(sanitized)
            except Exception as ex:
                logger.debug(f"[AnalysisOrchestrator] Skipping invalid correction item: {ex}")

        # 4. Multi-Stage Pipeline Analyzers
        # Naturalness layer
        evaluated_corrections = NaturalnessAnalyzer.evaluate_naturalness(
            parsed_corrections,
            persona_style=input_data.persona_style,
        )

        # Context layer
        context_notes_from_ai = [
            ContextNote(
                persona_role=cn.get("persona_role"),
                formality_level=cn.get("formality_level", "appropriate"),
                observation=cn.get("observation", ""),
            )
            for cn in raw_data.get("context_notes", [])
        ]
        context_rule_notes, evaluated_corrections = ContextAnalyzer.evaluate_context_appropriateness(
            persona_role=input_data.persona_role,
            user_transcript=clean_text,
            corrections=evaluated_corrections,
        )
        all_context_notes = context_notes_from_ai + context_rule_notes

        # Grammar and Vocabulary Miner
        raw_grammar = [
            GrammarPointNote(
                grammar_pattern=gp.get("grammar_pattern", ""),
                user_usage=gp.get("user_usage", ""),
                correct_usage=gp.get("correct_usage", ""),
                short_explanation=gp.get("short_explanation", ""),
                example_sentence=gp.get("example_sentence"),
            )
            for gp in raw_data.get("grammar_points", [])
            if gp.get("grammar_pattern")
        ]
        processed_grammar = GrammarAnalyzer.process_grammar_points(raw_grammar)

        raw_vocab = [
            VocabularyNote(
                original_word=vn.get("original_word", ""),
                suggested_alternatives=vn.get("suggested_alternatives", []),
                nuance_explanation=vn.get("nuance_explanation", ""),
                jlpt_level=vn.get("jlpt_level"),
            )
            for vn in raw_data.get("vocabulary_notes", [])
            if vn.get("original_word")
        ]
        processed_vocab = VocabularyAnalyzer.process_vocabulary_notes(raw_vocab)

        # 5. Feedback Prioritization & Budgeting
        priority_items = FeedbackPrioritizer.prioritize(
            corrections=evaluated_corrections,
            max_budget=self.policy.max_corrections_per_turn,
            mode=input_data.conversation_mode,
        )

        return TurnAnalysisResult(
            turn_id=input_data.current_turn_id,
            session_id=input_data.session_id,
            overall_quality_score=quality_score,
            communicative_success=success,
            strengths=strengths,
            corrections=evaluated_corrections,
            grammar_points=processed_grammar,
            vocabulary_notes=processed_vocab,
            context_notes=all_context_notes,
            priority_issues=priority_items,
            is_suspicious_transcript=is_suspicious,
            prompt_version=PROMPT_VERSION_TURN_ANALYSIS,
            analyzer_version="1.0.0",
            provider=provider_used,
            model=model_used,
            analyzed_at=datetime.now(timezone.utc),
        )

    async def analyze_session(
        self,
        session_id: str,
        persona_name: str,
        mode: str,
        turns_summary: list[dict[str, Any]],
        corrections_summary: list[dict[str, Any]],
        user_id: str | None = None,
    ) -> SessionAnalysisResult:
        """Performs whole-session holistic assessment, strength finding, and repeated mistake clustering."""
        user_turns_count = len([t for t in turns_summary if t.get("speaker") == "user"])

        # Build Session AI Request
        user_msg = PromptBuilder.build_session_analysis_user_message(
            persona_name=persona_name,
            mode=mode,
            turns_summary=turns_summary,
            corrections_summary=corrections_summary,
        )

        ai_request = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=user_msg)],
            system_instruction=SESSION_ANALYSIS_SYSTEM_PROMPT,
            task=AITask.SESSION_ANALYSIS,
            temperature=0.3,
            response_format=ResponseFormat(
                type=ResponseFormatType.JSON_SCHEMA,
                json_schema=SESSION_ANALYSIS_JSON_SCHEMA,
            ),
        )

        try:
            ai_response: AIResponse = await self.ai_router.generate(
                task=AITask.SESSION_ANALYSIS,
                request=ai_request,
                user_id=user_id,
            )
            raw_data = self._parse_json_response(ai_response.text)
            provider_used = ai_response.provider
            model_used = ai_response.model
        except Exception as e:
            logger.warning(f"[AnalysisOrchestrator] Session AI analysis failed: {e}")
            raw_data = {}
            provider_used = "fallback"
            model_used = "fallback"

        # Detect repeated patterns via domain logic
        repeated_from_rules = SessionAnalyzer.detect_repeated_patterns(turns_summary, corrections_summary)
        repeated_from_ai = raw_data.get("repeated_issues", [])
        combined_repeated = repeated_from_rules + [r for r in repeated_from_ai if r not in repeated_from_rules]

        # Counts
        must_fix_cnt = len([c for c in corrections_summary if c.get("severity") == "MUST_FIX"])
        should_fix_cnt = len([c for c in corrections_summary if c.get("severity") == "SHOULD_FIX"])
        native_cnt = len([c for c in corrections_summary if c.get("severity") == "NATIVE_ALTERNATIVE"])

        res = SessionAnalysisResult(
            session_id=session_id,
            overall_score=raw_data.get("overall_score", 78),
            strengths=raw_data.get("strengths", []),
            weaknesses=raw_data.get("weaknesses", ["Tiếp tục cải thiện độ tự nhiên của trợ từ."]),
            repeated_issues=combined_repeated,
            top_recommendations=raw_data.get(
                "top_recommendations",
                [
                    "Thực hành chia thể động từ chuẩn xác trong câu nối.",
                    "Lắng nghe và lặp lại các câu khẩu ngữ tự nhiên của Persona.",
                    "Duy trì thói quen nói trọn vẹn câu trước khi kết thúc.",
                ],
            )[:3],
            total_user_turns_analyzed=user_turns_count,
            total_corrections_count=len(corrections_summary),
            must_fix_count=must_fix_cnt,
            should_fix_count=should_fix_cnt,
            native_alt_count=native_cnt,
            grammar_summary=raw_data.get("grammar_summary", []),
            vocabulary_summary=raw_data.get("vocabulary_summary", []),
            prompt_version=PROMPT_VERSION_SESSION_ANALYSIS,
            analyzer_version="1.0.0",
            provider=provider_used,
            model=model_used,
            analyzed_at=datetime.now(timezone.utc),
        )

        return SessionAnalyzer.ensure_strengths(res, user_turns_count)

    def _parse_json_response(self, text: str) -> dict[str, Any]:
        """Safely parses structured JSON string with fallback markdown strip."""
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try finding first { and last }
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(cleaned[start : end + 1])
                except Exception:
                    pass
            return {}
