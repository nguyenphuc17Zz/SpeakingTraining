import time
from typing import Any

from app.core.logging import logger
from app.domains.pronunciation.analyzers.intonation_analyzer import IntonationAnalyzer
from app.domains.pronunciation.analyzers.mora_timing_analyzer import MoraTimingAnalyzer
from app.domains.pronunciation.analyzers.phoneme_analyzer import PhonemeAnalyzer
from app.domains.pronunciation.analyzers.pitch_analyzer import PitchAnalyzerComponent
from app.domains.pronunciation.analyzers.rhythm_analyzer import RhythmAnalyzer
from app.domains.pronunciation.contracts import (
    AnalysisConfidenceLevel,
    AudioQualityReport,
    PronunciationAnalysisPolicy,
    PronunciationResult,
    PronunciationTarget,
    ReferenceType,
)
from app.domains.pronunciation.feedback.feedback_generator import PronunciationFeedbackGenerator
from app.domains.pronunciation.infrastructure.alignment_engine import AlignmentEngine
from app.domains.pronunciation.infrastructure.audio_preprocessor import AudioPreprocessor
from app.domains.pronunciation.infrastructure.audio_quality_analyzer import AudioQualityAnalyzer
from app.domains.pronunciation.infrastructure.pitch_extractor import PitchExtractor
from app.domains.pronunciation.infrastructure.vad_analyzer import VADAnalyzer
from app.domains.pronunciation.japanese.mora_analyzer import JapaneseMoraAnalyzer
from app.domains.pronunciation.japanese.reading_resolver import JapaneseReadingResolver
from app.domains.pronunciation.scoring.scorer import PronunciationScorer
from app.domains.speech.contracts import WordTimestamp


class PronunciationPipeline:
    """End-to-end multi-stage Japanese pronunciation analysis pipeline with graceful partial degradation."""

    ENGINE_VERSION = "1.0.0"

    @classmethod
    async def run(
        cls,
        audio_bytes: bytes,
        target: PronunciationTarget,
        user_transcript: str | None = None,
        word_timestamps: list[WordTimestamp] | None = None,
        policy: PronunciationAnalysisPolicy = PronunciationAnalysisPolicy.DEEP,
    ) -> PronunciationResult:
        """
        Executes full audio preprocessing, VAD, alignment, acoustic analyzers, and scoring.
        """
        start_pipeline = time.perf_counter()
        partial_reasons: list[str] = []

        # 1. Preprocess audio
        samples, sr, duration_sec = AudioPreprocessor.load_and_preprocess(audio_bytes)
        duration_ms = int(duration_sec * 1000)

        # 2. Audio Quality Validation
        quality_report = AudioQualityAnalyzer.analyze_quality(samples, sr)
        if not quality_report.is_usable:
            logger.warning(
                f"[PronunciationPipeline] Audio quality check failed: {quality_report.issues}"
            )
            top_issues, strengths, rec = PronunciationFeedbackGenerator.generate(
                phoneme_assessments=None,
                mora_assessment=None,
                pitch_assessment=None,
                rhythm_assessment=None,
                intonation_assessment=None,
            )
            return PronunciationScorer.calculate_overall(
                phoneme_comp=None,
                mora_comp=None,
                pitch_comp=None,
                rhythm_comp=None,
                intonation_comp=None,
                phoneme_assessment=None,
                mora_assessment=None,
                pitch_assessment=None,
                rhythm_assessment=None,
                intonation_assessment=None,
                audio_quality=quality_report,
                top_issues=top_issues,
                strengths=[],
                practice_recommendation=quality_report.guidance or "Vui lòng thu âm lại rõ hơn.",
                reference_type=target.reference_type,
                partial_reasons=quality_report.issues,
            )

        # 3. VAD Segmentation
        vad_info = VADAnalyzer.analyze(samples, sr)
        speech_start_ms = vad_info["speech_start_ms"]
        speech_end_ms = max(speech_start_ms + 100, vad_info["speech_end_ms"])
        total_speech_ms = max(100, vad_info["total_speech_ms"])
        pauses = vad_info["pauses"]

        # 4. Japanese Reading & Mora Segmentation
        target_hiragana = JapaneseReadingResolver.to_hiragana(target.reference_text)
        target_moras = JapaneseMoraAnalyzer.segment_moras(target_hiragana)

        # 5. Alignment Engine
        try:
            alignment = AlignmentEngine.align(
                target_text=target.reference_text,
                speech_start_ms=speech_start_ms,
                speech_end_ms=speech_end_ms,
                word_timestamps=word_timestamps,
                user_transcript=user_transcript,
            )
            aligned_moras = alignment.mora_units
            alignment_conf = alignment.confidence_level
        except Exception as e:
            logger.warning(f"[PronunciationPipeline] Alignment error: {e}")
            aligned_moras = target_moras
            alignment_conf = AnalysisConfidenceLevel.LOW
            partial_reasons.append(f"Alignment error: {str(e)}")

        # 6. Stage Analyzers
        # 6a. Phoneme Analyzer
        try:
            phoneme_comp, phoneme_assessments = PhonemeAnalyzer.analyze(
                target_moras=target_moras,
                user_transcript=user_transcript,
                alignment_confidence=alignment_conf,
            )
        except Exception as e:
            logger.error(f"[PronunciationPipeline] Phoneme analyzer failed: {e}", exc_info=True)
            phoneme_comp = None
            phoneme_assessments = None
            partial_reasons.append(f"Phoneme analysis failed: {str(e)}")

        # 6b. Mora Timing Analyzer
        try:
            mora_comp, mora_assessment = MoraTimingAnalyzer.analyze(
                aligned_moras=aligned_moras,
                total_speech_ms=total_speech_ms,
                alignment_confidence=alignment_conf,
            )
        except Exception as e:
            logger.error(f"[PronunciationPipeline] Mora timing analyzer failed: {e}", exc_info=True)
            mora_comp = None
            mora_assessment = None
            partial_reasons.append(f"Mora timing analysis failed: {str(e)}")

        # 6c. Pitch Extractor & Pitch Analyzer
        pitch_comp = None
        pitch_assessment = None
        pitch_curve = None
        try:
            pitch_curve = PitchExtractor.extract_f0(samples, sr)
            pitch_comp, pitch_assessment = PitchAnalyzerComponent.analyze(
                target_text=target.reference_text,
                pitch_curve=pitch_curve,
                aligned_moras=aligned_moras,
                speech_start_ms=speech_start_ms,
                alignment_confidence=alignment_conf,
            )
        except Exception as e:
            logger.error(f"[PronunciationPipeline] Pitch analysis failed: {e}", exc_info=True)
            partial_reasons.append(f"Pitch analysis failed: {str(e)}")

        # 6d. Rhythm Analyzer
        try:
            rhythm_comp, rhythm_assessment = RhythmAnalyzer.analyze(
                aligned_moras=aligned_moras,
                total_speech_ms=total_speech_ms,
                pauses=pauses,
                alignment_confidence=alignment_conf,
            )
        except Exception as e:
            logger.error(f"[PronunciationPipeline] Rhythm analyzer failed: {e}", exc_info=True)
            rhythm_comp = None
            rhythm_assessment = None
            partial_reasons.append(f"Rhythm analysis failed: {str(e)}")

        # 6e. Intonation Analyzer
        try:
            intonation_comp, intonation_assessment = IntonationAnalyzer.analyze(
                target_text=target.reference_text,
                pitch_curve=pitch_curve,
                speech_end_ms=speech_end_ms,
                alignment_confidence=alignment_conf,
            )
        except Exception as e:
            logger.error(f"[PronunciationPipeline] Intonation analyzer failed: {e}", exc_info=True)
            intonation_comp = None
            intonation_assessment = None
            partial_reasons.append(f"Intonation analysis failed: {str(e)}")

        # 7. Feedback Generation & Prioritization
        top_issues, strengths, recommendation = PronunciationFeedbackGenerator.generate(
            phoneme_assessments=phoneme_assessments,
            mora_assessment=mora_assessment,
            pitch_assessment=pitch_assessment,
            rhythm_assessment=rhythm_assessment,
            intonation_assessment=intonation_assessment,
        )

        # 8. Multi-component Aggregated Scoring
        result = PronunciationScorer.calculate_overall(
            phoneme_comp=phoneme_comp,
            mora_comp=mora_comp,
            pitch_comp=pitch_comp,
            rhythm_comp=rhythm_comp,
            intonation_comp=intonation_comp,
            phoneme_assessment=phoneme_assessments,
            mora_assessment=mora_assessment,
            pitch_assessment=pitch_assessment,
            rhythm_assessment=rhythm_assessment,
            intonation_assessment=intonation_assessment,
            audio_quality=quality_report,
            top_issues=top_issues,
            strengths=strengths,
            practice_recommendation=recommendation,
            reference_type=target.reference_type,
            partial_reasons=partial_reasons,
        )

        duration_pipeline_ms = int((time.perf_counter() - start_pipeline) * 1000)
        logger.info(
            f"[PronunciationPipeline] Completed in {duration_pipeline_ms}ms (Score: {result.overall_score}, Conf: {result.overall_confidence.value})"
        )

        return result
