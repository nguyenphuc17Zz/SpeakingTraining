import re
from typing import Any

from app.domains.shadowing.contracts import (
    CandidateCategory,
    ShadowingCandidate,
    SpeakingDifficulty,
    TranscriptSegmentDTO,
)


class ShadowingCandidateSelector:
    """
    Selects, scores, and tags the highest-learning-value shadowing candidates
    tailored to the learner's specific profile, goals, and pronunciation/grammar weaknesses.
    """

    _LONG_VOWEL_RE = re.compile(
        r"([あかさたなはまやらわがざだばぱ][あ]|"
        r"[いきしちにひみりぎじぢびぴ][い]|"
        r"[うくすつぬふむゆるぐずづぶぷゅ][う]|"
        r"[えけせてねへめれげぜでべぺ][い]|"
        r"[えけせてねへめれげぜでべぺ][え]|"
        r"[おこそとのほもよろごぞどぼぽょ][う]|"
        r"[おこそとのほもよろごぞどぼぽょ][お]|"
        r"[ー〜])"
    )
    _SMALL_TSU_RE = re.compile(r"(っ|ッ)")
    _KEIGO_RE = re.compile(r"(ございます|いらっしゃ|おっしゃ|申し上げ|いたします|存じ|賜り|拝見|恐れ入)")

    @classmethod
    def select_candidates(
        cls,
        segments: list[TranscriptSegmentDTO],
        learner_goals: list[str] | None = None,
        learner_weaknesses: list[dict[str, Any] | str] | None = None,
        max_recommendations: int = 8,
    ) -> list[ShadowingCandidate]:
        """
        Ranks all segments and returns top recommended candidates with explainable pedagogical reasons.
        """
        if not segments:
            return []

        goals_str = " ".join([str(g).lower() for g in (learner_goals or [])])
        weaknesses_list: list[str] = []
        if learner_weaknesses:
            for w in learner_weaknesses:
                if isinstance(w, dict):
                    weaknesses_list.append(w.get("statement", "") or w.get("key", ""))
                else:
                    weaknesses_list.append(str(w))
        weakness_str = " ".join(weaknesses_list).lower()

        # Check learner targets
        has_workplace_target = "workplace" in goals_str or "keigo" in goals_str or "kính ngữ" in goals_str or "công việc" in goals_str
        has_long_vowel_weakness = "long_vowel" in weakness_str or "trường âm" in weakness_str or "chouon" in weakness_str or "vowel" in weakness_str
        has_sokuon_weakness = "sokuon" in weakness_str or "âm ngắt" in weakness_str or "small_tsu" in weakness_str
        has_naturalness_target = "naturalness" in goals_str or "tự nhiên" in goals_str or "ending" in weakness_str

        candidates: list[ShadowingCandidate] = []

        for seg in segments:
            text = seg.normalized_text
            dur = seg.duration or max(0.5, seg.end_time - seg.start_time)
            diff = seg.difficulty

            # 1. Filter out non-viable candidates
            if dur < 1.0 or len(text) < 4:
                continue
            if dur > 16.0:
                continue
            if seg.confidence < 0.4:
                continue

            # 2. Compute base score
            # Ideal shadowing length is 2.5s - 7.5s
            length_score = 1.0 - min(0.5, abs(dur - 4.5) / 10.0)
            linguistic_score = min(1.0, (len(seg.vocabulary) * 0.2) + (len(seg.grammar) * 0.3) + (len(seg.expressions) * 0.3) + 0.3)
            base_score = (length_score * 0.4) + (linguistic_score * 0.6)

            categories: list[CandidateCategory] = []
            reasons: list[str] = []
            target_skill = "fluency"
            matched_weakness: str | None = None
            matched_goal: str | None = None

            # 3. Learner Matching Boosts
            reading_text = (seg.reading or "") + " " + text

            # Long vowels check
            long_vowel_matches = len(cls._LONG_VOWEL_RE.findall(reading_text))
            if long_vowel_matches > 0:
                categories.append(CandidateCategory.BEST_FOR_PRONUNCIATION)
                if has_long_vowel_weakness:
                    base_score += min(0.65, 0.25 + (long_vowel_matches * 0.12))
                    reasons.append("Chứa các từ có trường âm giúp khắc phục điểm yếu phát âm hiện tại của bạn")
                    target_skill = "pronunciation"
                    matched_weakness = "long_vowels"
                else:
                    reasons.append("Rèn luyện trường âm và ngắt nhịp rõ ràng")

            # Small tsu (sokuon) check
            sokuon_matches = len(cls._SMALL_TSU_RE.findall(reading_text))
            if sokuon_matches > 0 and has_sokuon_weakness:
                base_score += min(0.50, 0.20 + (sokuon_matches * 0.10))
                if CandidateCategory.BEST_FOR_PRONUNCIATION not in categories:
                    categories.append(CandidateCategory.BEST_FOR_PRONUNCIATION)
                reasons.append("Luyện tập kiểm soát độ dài âm ngắt (っ)")
                target_skill = "pronunciation"
                matched_weakness = "sokuon"

            # Keigo / Workplace check
            keigo_matches = len(cls._KEIGO_RE.findall(text))
            if keigo_matches > 0:
                categories.append(CandidateCategory.BEST_FOR_WORKPLACE)
                if has_workplace_target:
                    base_score += min(0.65, 0.30 + (keigo_matches * 0.10))
                    reasons.append("Phù hợp với mục tiêu giao tiếp công việc & kính ngữ (keigo)")
                    target_skill = "workplace"
                    matched_goal = "workplace_japanese"
                else:
                    reasons.append("Luyện phản xạ mẫu câu kính ngữ chuẩn mực")

            # Natural expressions check
            if seg.expressions:
                categories.append(CandidateCategory.BEST_FOR_NATURALNESS)
                if has_naturalness_target:
                    base_score += 0.25
                    reasons.append(f"Chứa biểu cảm khẩu ngữ tự nhiên ({seg.expressions[0].expression})")
                    target_skill = "naturalness"
                else:
                    reasons.append("Luyện tập các từ nối và đuôi câu tự nhiên của người bản xứ")

            # Speed check
            mora_rate = diff.speed_mora_per_sec if diff else 6.0
            if mora_rate >= 7.5:
                categories.append(CandidateCategory.BEST_FOR_SPEED)
                categories.append(CandidateCategory.BEST_FOR_CHALLENGE)
                reasons.append(f"Thử thách tốc độ cao ({mora_rate} mora/s) nâng cao phản xạ nghe-nói")
            elif mora_rate <= 5.0 and len(text) <= 18:
                categories.append(CandidateCategory.BEST_FOR_BEGINNER)
                reasons.append("Câu ngắn, phát âm chậm rãi, thích hợp bắt đầu buổi luyện")

            # Fallback reason
            if not reasons:
                reasons.append("Mẫu câu hội thoại thông dụng, độ dài lý tưởng cho bài tập shadowing")

            final_score = round(min(1.0, max(0.1, base_score)), 2)
            main_reason = " • ".join(reasons[:2])

            # Update segment DTO metadata
            seg.candidate_categories = categories
            seg.recommendation_score = final_score
            seg.recommendation_reason = main_reason

            if categories and final_score >= 0.5:
                candidates.append(
                    ShadowingCandidate(
                        segment_id=seg.id,
                        video_id=seg.video_id,
                        start_time=seg.start_time,
                        end_time=seg.end_time,
                    text=seg.normalized_text,
                    reading=seg.reading,
                    speaker_id=seg.speaker_id,
                    score=final_score,
                    categories=categories,
                    reason=main_reason,
                    target_skill=target_skill,
                    difficulty=diff.overall_difficulty if diff else SpeakingDifficulty.NORMAL,
                    matched_weakness=matched_weakness,
                    matched_goal=matched_goal,
                )
            )

        # Sort descending by personalized recommendation score
        candidates.sort(key=lambda c: c.score, reverse=True)

        return candidates[:max_recommendations]
