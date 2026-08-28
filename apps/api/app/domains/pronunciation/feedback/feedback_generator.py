from app.domains.pronunciation.contracts import (
    IntonationAssessment,
    MoraTimingAssessment,
    PhonemeAssessment,
    PitchAssessment,
    PronunciationFeedbackItem,
    RhythmAssessment,
)
from app.domains.pronunciation.feedback.feedback_prioritizer import PronunciationFeedbackPrioritizer
from app.domains.pronunciation.japanese.issue_taxonomy import JapaneseIssueType, TAXONOMY_EXPLANATIONS


class PronunciationFeedbackGenerator:
    """Generates structured, user-friendly pronunciation feedback items and strengths."""

    @classmethod
    def generate(
        cls,
        phoneme_assessments: list[PhonemeAssessment] | None,
        mora_assessment: MoraTimingAssessment | None,
        pitch_assessment: PitchAssessment | None,
        rhythm_assessment: RhythmAssessment | None,
        intonation_assessment: IntonationAssessment | None,
    ) -> tuple[list[PronunciationFeedbackItem], list[str], str | None]:
        """
        Produces:
            - top_issues: list[PronunciationFeedbackItem] (sorted by priority)
            - strengths: list[str]
            - practice_recommendation: str | None
        """
        raw_issues: list[PronunciationFeedbackItem] = []
        strengths: list[str] = []

        # 1. Phoneme Issues & Strengths
        if phoneme_assessments:
            clean_phonemes = True
            for pa in phoneme_assessments:
                if pa.issue_type:
                    clean_phonemes = False
                    # Lookup taxonomy
                    issue_enum = cls._match_issue_enum(pa.issue_type)
                    meta = TAXONOMY_EXPLANATIONS.get(
                        issue_enum,
                        {
                            "title": f"Âm「{pa.kana}」",
                            "explanation": f"Cách phát âm「{pa.kana}」cần chỉnh lại cho chuẩn tiếng Nhật.",
                            "practice_tip": pa.tip or "Luyện nghe và nhắc lại theo giọng mẫu.",
                        },
                    )
                    raw_issues.append(
                        PronunciationFeedbackItem(
                            issue_key=pa.issue_type,
                            category="phoneme",
                            severity="MUST_FIX" if pa.score < 65 else "SHOULD_FIX",
                            title=meta["title"],
                            explanation=meta["explanation"],
                            practice_tip=pa.tip or meta["practice_tip"],
                            target_snippet=pa.kana,
                            detected_snippet=pa.detected_sound_category,
                        )
                    )
            if clean_phonemes:
                strengths.append("Phát âm các phụ âm và nguyên âm rõ ràng, chuẩn xác.")

        # 2. Mora Timing Issues & Strengths
        if mora_assessment:
            if mora_assessment.overall_score >= 88:
                strengths.append("Nhịp điệu và độ dài các mora (âm tiết) rất đều đặn và tự nhiên.")
            elif mora_assessment.top_timing_issues:
                for t_issue in mora_assessment.top_timing_issues:
                    if "っ" in t_issue:
                        meta = TAXONOMY_EXPLANATIONS[JapaneseIssueType.SMALL_TSU]
                        raw_issues.append(
                            PronunciationFeedbackItem(
                                issue_key=JapaneseIssueType.SMALL_TSU.value,
                                category="mora_timing",
                                severity="MUST_FIX",
                                title=meta["title"],
                                explanation=meta["explanation"],
                                practice_tip=meta["practice_tip"],
                                target_snippet="っ",
                            )
                        )
                    elif "Trường âm" in t_issue:
                        meta = TAXONOMY_EXPLANATIONS[JapaneseIssueType.LONG_VOWEL]
                        raw_issues.append(
                            PronunciationFeedbackItem(
                                issue_key=JapaneseIssueType.LONG_VOWEL.value,
                                category="mora_timing",
                                severity="MUST_FIX",
                                title=meta["title"],
                                explanation=meta["explanation"],
                                practice_tip=meta["practice_tip"],
                            )
                        )
                    elif "ん" in t_issue:
                        meta = TAXONOMY_EXPLANATIONS[JapaneseIssueType.N_SOUND]
                        raw_issues.append(
                            PronunciationFeedbackItem(
                                issue_key=JapaneseIssueType.N_SOUND.value,
                                category="mora_timing",
                                severity="SHOULD_FIX",
                                title=meta["title"],
                                explanation=meta["explanation"],
                                practice_tip=meta["practice_tip"],
                                target_snippet="ん",
                            )
                        )

        # 3. Pitch Accent Issues & Strengths
        if pitch_assessment and pitch_assessment.confidence >= 0.5:
            if pitch_assessment.pattern_matched:
                strengths.append(
                    f"Cao độ trọng âm chuẩn xác theo quy tắc Tokyo ({pitch_assessment.accent_pattern_target.value})."
                )
            else:
                target_pat = pitch_assessment.accent_pattern_target
                issue_key = f"pitch_accent.{target_pat.value}"
                issue_enum = cls._match_issue_enum(issue_key) or JapaneseIssueType.PITCH_GENERAL
                meta = TAXONOMY_EXPLANATIONS.get(
                    issue_enum,
                    {
                        "title": f"Cao độ {target_pat.value}",
                        "explanation": f"Cao độ từ này chuẩn Tokyo là {target_pat.value}.",
                        "practice_tip": "Hãy chú ý hạ hoặc lên giọng đúng ở mora trọng tâm.",
                    },
                )
                raw_issues.append(
                    PronunciationFeedbackItem(
                        issue_key=issue_key,
                        category="pitch",
                        severity="SHOULD_FIX",
                        title=meta["title"],
                        explanation=pitch_assessment.explanation or meta["explanation"],
                        practice_tip=meta["practice_tip"],
                        target_snippet=target_pat.value,
                        detected_snippet=pitch_assessment.accent_pattern_observed.value,
                    )
                )

        # 4. Rhythm & Fluency
        if rhythm_assessment:
            if rhythm_assessment.speech_rate_mora_per_sec > 0:
                if 4.2 <= rhythm_assessment.speech_rate_mora_per_sec <= 6.5 and rhythm_assessment.hesitation_count == 0:
                    strengths.append(
                        f"Tốc độ nói mượt mà ({rhythm_assessment.speech_rate_mora_per_sec} mora/giây), không ngập ngừng."
                    )
                elif rhythm_assessment.speech_rate_mora_per_sec < 3.5:
                    raw_issues.append(
                        PronunciationFeedbackItem(
                            issue_key="rhythm.slow_tempo",
                            category="rhythm",
                            severity="NATIVE_ALTERNATIVE",
                            title="Tốc độ nói (Tempo)",
                            explanation=f"Tốc độ hiện tại ({rhythm_assessment.speech_rate_mora_per_sec} mora/s) hơi chậm so với nhịp giao tiếp thông thường.",
                            practice_tip="Luyện nói liền mạch theo nhịp đếm 1-2-3-4 để tăng độ trôi chảy.",
                        )
                    )

        # 5. Intonation
        if intonation_assessment and intonation_assessment.confidence >= 0.5:
            if not intonation_assessment.is_sentence_final_natural:
                raw_issues.append(
                    PronunciationFeedbackItem(
                        issue_key=f"intonation.{intonation_assessment.sentence_final_type}",
                        category="intonation",
                        severity="SHOULD_FIX",
                        title="Ngữ điệu cuối câu (Sentence-final)",
                        explanation=intonation_assessment.explanation or "Ngữ điệu cuối câu cần tự nhiên hơn.",
                        practice_tip="Lắng nghe ngữ điệu lên/xuống giọng ở âm cuối của câu mẫu.",
                    )
                )

        # Prioritize top 3
        top_issues = PronunciationFeedbackPrioritizer.prioritize(raw_issues, max_items=3)

        # Practice recommendation summary
        if top_issues:
            practice_recommendation = f"Tập trung cải thiện: {top_issues[0].title} — {top_issues[0].practice_tip}"
        elif strengths:
            practice_recommendation = "Phát âm rất tốt! Tiếp tục duy trì phong độ và thử sức với các câu dài hơn."
        else:
            practice_recommendation = "Hãy thử thu âm lại trong môi trường yên tĩnh hơn để có phân tích chi tiết."

        return top_issues, strengths, practice_recommendation

    @staticmethod
    def _match_issue_enum(key: str) -> JapaneseIssueType | None:
        for it in JapaneseIssueType:
            if it.value == key:
                return it
        return None
