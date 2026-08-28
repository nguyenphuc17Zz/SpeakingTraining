import uuid
from typing import Any

from app.domains.shadowing.contracts import (
    CandidateCategory,
    ShadowingCandidate,
    ShadowingLesson,
    SpeakingDifficulty,
    TranscriptSegmentDTO,
)


class ShadowingLessonGenerator:
    """Generates structured, time-bounded shadowing lessons from YouTube video content."""

    @classmethod
    def generate_lesson(
        cls,
        video_id: str,
        video_title: str,
        segments: list[TranscriptSegmentDTO],
        recommended_candidates: list[ShadowingCandidate],
        time_budget_minutes: int = 15,
        mode: str = "quick_shadow",
    ) -> ShadowingLesson:
        """
        Assembles a focused lesson according to target time budget and mode.
        """
        # Map time budget to number of segments (each segment takes ~2-3 minutes of active shadowing)
        clip_count = max(3, min(12, time_budget_minutes // 2))

        # Select candidate segment IDs
        seg_dict = {s.id: s for s in segments}
        selected_segments: list[TranscriptSegmentDTO] = []

        if mode == "pronunciation_focus":
            target_cats = [CandidateCategory.BEST_FOR_PRONUNCIATION]
            title = f"Luyện phát âm & ngữ điệu — {video_title[:30]}"
            goal = "Tập trung kiểm soát trường âm, âm ngắt, và cao độ pitch accent chuẩn xác."
        elif mode == "naturalness_focus":
            target_cats = [CandidateCategory.BEST_FOR_NATURALNESS]
            title = f"Luyện biểu cảm & khẩu ngữ — {video_title[:30]}"
            goal = "Bắt chước các đuôi câu, từ đệm và ngữ khí hội thoại tự nhiên."
        elif mode == "speed_challenge":
            target_cats = [CandidateCategory.BEST_FOR_SPEED, CandidateCategory.BEST_FOR_CHALLENGE]
            title = f"Thử thách tốc độ bản xứ — {video_title[:30]}"
            goal = "Nâng cao tốc độ phản xạ và sự linh hoạt của cơ miệng ở tốc độ nói nhanh."
        elif mode == "deep_shadow":
            target_cats = [CandidateCategory.BEST_FOR_WORKPLACE, CandidateCategory.BEST_FOR_PRONUNCIATION]
            title = f"Shadowing chuyên sâu — {video_title[:30]}"
            goal = "Phân tích ngữ pháp, từ vựng và luyện tập nhiều lần từng câu đến mức thuần thục."
        else:  # quick_shadow
            target_cats = []
            title = f"Quick Shadowing — {video_title[:30]}"
            goal = "Luyện phản xạ nhanh với các câu hội thoại tiêu biểu nhất của video."

        # Filter candidates by preferred categories if specified
        matched_cands = [c for c in recommended_candidates if not target_cats or any(cat in c.categories for cat in target_cats)]
        if not matched_cands:
            matched_cands = recommended_candidates

        # Pick top candidates
        chosen_cand_ids = [c.segment_id for c in matched_cands[:clip_count]]
        for cid in chosen_cand_ids:
            if cid in seg_dict:
                selected_segments.append(seg_dict[cid])

        # Fallback if candidates were insufficient
        if len(selected_segments) < 3 and segments:
            for s in segments[:clip_count]:
                if s not in selected_segments:
                    selected_segments.append(s)

        # Order segments: chronological or easy -> hard
        if mode != "speed_challenge":
            selected_segments.sort(key=lambda s: (s.difficulty.overall_difficulty.value if s.difficulty else "normal", s.sequence))
        else:
            selected_segments.sort(key=lambda s: s.sequence)

        return ShadowingLesson(
            id=f"lesson_{uuid.uuid4().hex[:12]}",
            video_id=video_id,
            title=title,
            goal=goal,
            mode=mode,
            estimated_minutes=time_budget_minutes,
            difficulty=SpeakingDifficulty.NORMAL,
            segments=selected_segments,
        )
