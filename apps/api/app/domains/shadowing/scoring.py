import math
import re
from typing import Any
from pydantic import BaseModel, Field

from app.core.logging import logger
from app.domains.pronunciation.contracts import PronunciationResult
from app.domains.pronunciation.japanese.mora_analyzer import JapaneseMoraAnalyzer
from app.domains.pronunciation.japanese.reading_resolver import JapaneseReadingResolver


class MoraDiffToken(BaseModel):
    text: str
    reading: str | None = None
    type: str  # correct, incorrect, missing, extra
    expected: str | None = None


class ShadowingScoringMetrics(BaseModel):
    mora_accuracy: float = 0.0
    speech_rate_mora_sec: float = 0.0
    target_rate_mora_sec: float = 0.0
    tempo_score: float = 0.0
    pitch_score: float = 0.0
    fluency_score: float = 0.0
    overall_score: float = 0.0
    diff_tokens: list[MoraDiffToken] = Field(default_factory=list)


class ShadowingEvaluationResult(BaseModel):
    score: float
    accuracy_score: float
    timing_score: float
    pronunciation_score: float
    rhythm_score: float
    feedback: str
    strengths: list[str] = Field(default_factory=list)
    top_issues: list[dict[str, Any]] = Field(default_factory=list)
    metrics: ShadowingScoringMetrics
    success: bool = True
    mastery_state: str = "practicing"


class ShadowingScorer:
    """
    Production Deterministic Acoustic-Phonetic Scoring Engine for Japanese Shadowing.
    Executes sub-200ms local morphological and acoustic evaluation without external LLM calls.
    """

    @classmethod
    def evaluate(
        cls,
        target_text: str,
        user_transcript: str | None,
        target_duration_sec: float | None = None,
        user_duration_sec: float | None = None,
        pron_result: PronunciationResult | None = None,
        shadowing_mode: str = "shadow",
        playback_speed: float = 1.0,
        fallback_pron_score: float | None = None,
    ) -> ShadowingEvaluationResult:
        """
        Executes end-to-end multi-dimensional Shadowing scoring:
        1. Mora & Phoneme Levenshtein Alignment (Kanji/Kana normalized)
        2. Speech Rate & Tempo matching (Mora per sec ratio)
        3. Pitch Accent & Intonation extraction
        4. Fluency & Pause consistency
        5. Pedagogical feedback & actionable recommendations
        """
        clean_target = (target_text or "").strip()
        clean_user = (user_transcript or "").strip()

        # Handle Empty Audio / No Speech
        if not clean_user or clean_user == "(Chưa có âm thanh)" or clean_user.startswith("Audio length"):
            return ShadowingEvaluationResult(
                score=0.0,
                accuracy_score=0.0,
                timing_score=0.0,
                pronunciation_score=0.0,
                rhythm_score=0.0,
                feedback="Không nhận diện được giọng nói trong bản thu âm. Vui lòng kiểm tra micro hoặc nói to rõ hơn.",
                strengths=[],
                top_issues=[
                    {
                        "title": "Không phát hiện giọng nói",
                        "category": "Microphone / Âm thanh",
                        "explanation": "Whisper STT không nhận diện được tín hiệu phát âm nào từ bản thu âm.",
                        "practice_tip": "Kiểm tra micro và bấm thu âm lại khi bắt đầu nói.",
                    }
                ],
                metrics=ShadowingScoringMetrics(
                    mora_accuracy=0.0,
                    overall_score=0.0,
                    diff_tokens=[MoraDiffToken(text=clean_target, type="missing")],
                ),
                success=False,
                mastery_state="practicing",
            )

        # 1. Morphological Mora Alignment
        target_hira = JapaneseReadingResolver.to_hiragana(clean_target)
        user_hira = JapaneseReadingResolver.to_hiragana(clean_user)

        target_moras = [m.kana for m in JapaneseMoraAnalyzer.segment_moras(target_hira)]
        user_moras = [m.kana for m in JapaneseMoraAnalyzer.segment_moras(user_hira)]

        align_ops, diff_tokens = cls._align_mora_sequences(target_moras, user_moras, clean_target, clean_user)

        # 2. Compute Mora Accuracy (MER)
        num_target = max(1, len(target_moras))
        substitutions = sum(1 for op in align_ops if op[0] == "sub")
        deletions = sum(1 for op in align_ops if op[0] == "del")
        insertions = sum(1 for op in align_ops if op[0] == "ins")

        mer = (substitutions + deletions + (insertions * 0.5)) / float(num_target)
        accuracy_score = max(0.0, min(100.0, round((1.0 - min(1.0, mer)) * 100.0, 1)))

        # 3. Compute Speech Rate & Tempo Score
        effective_target_dur = target_duration_sec or (num_target / 5.5)
        # If user_duration_sec is missing or unrealistic (< 0.3s for multi-mora words, e.g. mock bytes), default gracefully
        if not user_duration_sec or user_duration_sec < 0.3:
            effective_user_dur = effective_target_dur
        else:
            effective_user_dur = user_duration_sec

        target_rate = round(num_target / max(0.4, effective_target_dur), 2)
        user_rate = round(max(1, len(user_moras)) / max(0.4, effective_user_dur), 2)

        expected_rate = target_rate * max(0.5, playback_speed)
        rate_ratio = user_rate / max(1.0, expected_rate)

        # Gaussian tempo score around 1.0 ratio
        tempo_penalty = math.exp(-((rate_ratio - 1.0) ** 2) / (2 * (0.22 ** 2)))
        tempo_score = round(max(0.0, min(100.0, tempo_penalty * 100.0)), 1)

        # 4. Pitch & Intonation Score
        pitch_score = fallback_pron_score if fallback_pron_score is not None else accuracy_score
        intonation_score = fallback_pron_score if fallback_pron_score is not None else accuracy_score
        rhythm_score = fallback_pron_score if fallback_pron_score is not None else accuracy_score

        if pron_result:
            if pron_result.pitch_score and pron_result.pitch_score.available:
                pitch_score = float(pron_result.pitch_score.score)
            if pron_result.intonation_score and pron_result.intonation_score.available:
                intonation_score = float(pron_result.intonation_score.score)
            if pron_result.rhythm_score and pron_result.rhythm_score.available:
                rhythm_score = float(pron_result.rhythm_score.score)
            if pron_result.rhythm_score and pron_result.rhythm_score.available:
                rhythm_score = float(pron_result.rhythm_score.score)

        pitch_combined = round((pitch_score * 0.6) + (intonation_score * 0.4), 1)

        # 5. Fluency & Timing Subscore
        fluency_score = round((rhythm_score * 0.5) + (tempo_score * 0.5), 1)

        # 6. Overall Weighted Score calculation based on Shadowing Mode
        if shadowing_mode == "shadow":
            # Pure Shadowing: Tempo & Fluency are heavily weighted
            w_acc, w_tempo, w_pitch, w_fluency = 0.30, 0.25, 0.25, 0.20
        else:
            # Listen & Shadow / Repeat: Accuracy & Pitch take precedence
            w_acc, w_tempo, w_pitch, w_fluency = 0.40, 0.15, 0.25, 0.20

        raw_overall = (
            (accuracy_score * w_acc)
            + (tempo_score * w_tempo)
            + (pitch_combined * w_pitch)
            + (fluency_score * w_fluency)
        )
        overall_score = round(max(0.0, min(100.0, raw_overall)), 1)

        # 7. Generate Issues & Pedagogical Feedback
        top_issues: list[dict[str, Any]] = []
        strengths: list[str] = []

        # Analyze Sokuon (っ)
        if "っ" in target_moras and "っ" not in user_moras:
            top_issues.append({
                "title": "Bỏ sót âm ngắt「っ」",
                "category": "Trường độ Mora",
                "explanation": "Câu có âm ngắt「っ」nhưng bản thu âm đã nuốt mất 1 nhịp dừng tĩnh.",
                "practice_tip": "Giữ khoảng lặng đúng 1 nhịp mora trước khi bật phụ âm tiếp theo.",
            })

        # Analyze Chōon (Long vowels)
        has_long_vowel_target = any(m in {"ー", "ああ", "いい", "うう", "ええ", "おお"} for m in target_moras)
        if has_long_vowel_target and substitutions > 0:
            top_issues.append({
                "title": "Chú ý trường âm (Long Vowels)",
                "category": "Âm vị & Mora",
                "explanation": "Đảm bảo ngân đủ 2 nhịp mora cho các nguyên âm kéo dài.",
                "practice_tip": "Đừng ngắt nguyên âm quá sớm, giữ đều hơi trong 2 nhịp.",
            })

        # Analyze Tempo / Speed
        if rate_ratio < 0.78:
            top_issues.append({
                "title": "Tốc độ nói hơi chậm so với bản xứ",
                "category": "Nhịp điệu Shadowing",
                "explanation": f"Tốc độ của bạn đạt {user_rate:.1f} mora/s (chuẩn video: {expected_rate:.1f} mora/s).",
                "practice_tip": "Nói đuổi sát theo video hơn, tránh dừng lại suy nghĩ giữa các cụm từ.",
            })
        elif rate_ratio > 1.30:
            top_issues.append({
                "title": "Tốc độ nói hơi vội",
                "category": "Nhịp điệu Shadowing",
                "explanation": f"Tốc độ của bạn ({user_rate:.1f} mora/s) nhanh hơn đáng kể so với người bản xứ.",
                "practice_tip": "Thả lỏng cơ hàm và giữ nhịp đều đặn theo người nói.",
            })

        # Strengths
        if accuracy_score >= 85:
            strengths.append("Độ chính xác từ vựng và âm vị xuất sắc.")
        if tempo_score >= 85:
            strengths.append(f"Tốc độ nói ({user_rate:.1f} mora/s) bám sát hoàn hảo người bản xứ.")
        if pitch_combined >= 80:
            strengths.append("Ngữ điệu và cao độ tự nhiên, rõ ràng.")

        # Overall Feedback text
        if overall_score >= 85:
            feedback = "Xuất sắc! (素晴らしい) Bạn phát âm chuẩn xác và bám nhịp video rất mượt mà."
        elif overall_score >= 70:
            feedback = "Rất tốt! (よくできました) Bạn nắm bắt tốt câu nói, hãy chú ý thêm một số điểm ngắt nhịp."
        elif overall_score >= 50:
            feedback = "Đã hoàn thành! Hãy thử nghe lại câu mẫu 1-2 lần rồi shadow lại để cải thiện nhịp điệu nhé."
        else:
            feedback = "Cần cải thiện. Hãy giảm tốc độ xuống 0.8x hoặc nghe kỹ từng cụm từ trước khi shadow."

        success = overall_score >= 70.0
        mastery_state = "comfortable" if overall_score >= 82.0 else ("practicing" if overall_score >= 50.0 else "struggling")

        # Merge acoustic issues from Pronunciation pipeline
        if pron_result and pron_result.top_issues:
            for item in pron_result.top_issues[:2]:
                dumped = item.model_dump() if hasattr(item, "model_dump") else (dict(item) if isinstance(item, dict) else {})
                if not any(i.get("title") == dumped.get("title") for i in top_issues):
                    top_issues.append(dumped)

        return ShadowingEvaluationResult(
            score=overall_score,
            accuracy_score=accuracy_score,
            timing_score=tempo_score,
            pronunciation_score=round(accuracy_score * 0.6 + pitch_combined * 0.4, 1),
            rhythm_score=fluency_score,
            feedback=feedback,
            strengths=strengths,
            top_issues=top_issues[:4],
            metrics=ShadowingScoringMetrics(
                mora_accuracy=accuracy_score,
                speech_rate_mora_sec=user_rate,
                target_rate_mora_sec=target_rate,
                tempo_score=tempo_score,
                pitch_score=pitch_combined,
                fluency_score=fluency_score,
                overall_score=overall_score,
                diff_tokens=diff_tokens,
            ),
            success=success,
            mastery_state=mastery_state,
        )

    @classmethod
    def _align_mora_sequences(
        cls,
        target_moras: list[str],
        user_moras: list[str],
        target_raw: str,
        user_raw: str,
    ) -> tuple[list[tuple[str, str | None, str | None]], list[MoraDiffToken]]:
        """
        Computes standard Levenshtein dynamic programming alignment between target and user moras.
        Returns:
          - align_ops: list of ('match'|'sub'|'del'|'ins', target_mora, user_mora)
          - diff_tokens: Tokenized list for UI rendering
        """
        n = len(target_moras)
        m = len(user_moras)

        # DP Table for Levenshtein Distance
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            dp[i][0] = i
        for j in range(m + 1):
            dp[0][j] = j

        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = 0 if cls._are_moras_equivalent(target_moras[i - 1], user_moras[j - 1]) else 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1,        # Deletion
                    dp[i][j - 1] + 1,        # Insertion
                    dp[i - 1][j - 1] + cost  # Match / Substitution
                )

        # Backtrack optimal alignment path
        i, j = n, m
        align_ops: list[tuple[str, str | None, str | None]] = []

        while i > 0 or j > 0:
            if i > 0 and j > 0:
                cost = 0 if cls._are_moras_equivalent(target_moras[i - 1], user_moras[j - 1]) else 1
                if dp[i][j] == dp[i - 1][j - 1] + cost:
                    op_type = "match" if cost == 0 else "sub"
                    align_ops.append((op_type, target_moras[i - 1], user_moras[j - 1]))
                    i -= 1
                    j -= 1
                    continue
            if i > 0 and dp[i][j] == dp[i - 1][j] + 1:
                align_ops.append(("del", target_moras[i - 1], None))
                i -= 1
                continue
            if j > 0 and dp[i][j] == dp[i][j - 1] + 1:
                align_ops.append(("ins", None, user_moras[j - 1]))
                j -= 1
                continue

        align_ops.reverse()

        # Build UI Diff Tokens
        diff_tokens: list[MoraDiffToken] = []
        for op, t_mora, u_mora in align_ops:
            if op == "match":
                diff_tokens.append(MoraDiffToken(text=u_mora or t_mora or "", type="correct"))
            elif op == "sub":
                diff_tokens.append(
                    MoraDiffToken(
                        text=u_mora or "",
                        type="incorrect",
                        expected=t_mora,
                    )
                )
            elif op == "del":
                diff_tokens.append(
                    MoraDiffToken(
                        text=t_mora or "",
                        type="missing",
                        expected=t_mora,
                    )
                )
            elif op == "ins":
                diff_tokens.append(
                    MoraDiffToken(
                        text=u_mora or "",
                        type="extra",
                    )
                )

        return align_ops, diff_tokens

    @staticmethod
    def _are_moras_equivalent(m1: str, m2: str) -> bool:
        """Checks if two moras are phonetically equivalent (handles voicing variations & long vowels)."""
        if m1 == m2:
            return True
        # Equivalence map for Japanese variations
        equivalents = {
            "じ": {"ぢ"}, "ぢ": {"じ"},
            "ず": {"づ"}, "づ": {"ず"},
            "ー": {"う", "お", "あ", "い", "え"},
            "を": {"お"}, "お": {"を"},
            "は": {"わ"},  # Topic marker は pronounced wa
            "へ": {"え"},  # Direction marker へ pronounced e
        }
        return m2 in equivalents.get(m1, set())
