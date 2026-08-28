from typing import Any

from app.domains.pronunciation.contracts import (
    AnalysisConfidenceLevel,
    MoraUnit,
    PhonemeAssessment,
    PronunciationScoreComponent,
)
from app.domains.pronunciation.japanese.issue_taxonomy import JapaneseIssueType, TAXONOMY_EXPLANATIONS
from app.domains.pronunciation.japanese.mora_analyzer import JapaneseMoraAnalyzer
from app.domains.pronunciation.japanese.reading_resolver import JapaneseReadingResolver


class PhonemeAnalyzer:
    """Evaluates Japanese phoneme articulation accuracy and detects sound substitution errors."""

    @classmethod
    def analyze(
        cls,
        target_moras: list[MoraUnit],
        user_transcript: str | None,
        alignment_confidence: AnalysisConfidenceLevel,
    ) -> tuple[PronunciationScoreComponent, list[PhonemeAssessment]]:
        """Analyzes phoneme production quality across all target moras."""
        if not target_moras:
            return (
                PronunciationScoreComponent(
                    score=100.0,
                    confidence=0.0,
                    weight=0.25,
                    available=False,
                    interpretation="Good",
                ),
                [],
            )

        if not user_transcript or not user_transcript.strip():
            return (
                PronunciationScoreComponent(
                    score=0.0,
                    confidence=1.0,
                    weight=0.25,
                    available=True,
                    interpretation="Needs Attention",
                ),
                [
                    PhonemeAssessment(
                        mora_index=tm.mora_index,
                        kana=tm.kana,
                        target_phonemes=tm.phonemes,
                        detected_sound_category=None,
                        score=0.0,
                        confidence=1.0,
                        issue_type=None,
                        tip=f"Chưa phát âm mora「{tm.kana}」.",
                    )
                    for tm in target_moras
                ],
            )

        user_hiragana = JapaneseReadingResolver.to_hiragana(user_transcript or "")
        user_moras = JapaneseMoraAnalyzer.segment_moras(user_hiragana)
        user_kana_list = [m.kana for m in user_moras]

        assessments: list[PhonemeAssessment] = []
        total_mora_score = 0.0

        for i, tm in enumerate(target_moras):
            kana = tm.kana
            target_phonemes = tm.phonemes

            # Check if user produced the exact kana at or near this position
            is_exact = False
            detected_kana = None
            if i < len(user_kana_list):
                detected_kana = user_kana_list[i]
                is_exact = (detected_kana == kana)
            elif kana in user_kana_list:
                is_exact = True
                detected_kana = kana

            # Check specific Japanese sound substitutions
            issue_type = None
            tip = None

            if not is_exact:
                if detected_kana:
                    # 1. R-sound confusion
                    if kana in {"ら", "り", "る", "れ", "ろ"}:
                        issue_type = JapaneseIssueType.PHONEME_R.value
                        tip = TAXONOMY_EXPLANATIONS[JapaneseIssueType.PHONEME_R]["practice_tip"]
                        mora_score = 65.0
                    # 2. Fu sound
                    elif kana == "ふ":
                        issue_type = JapaneseIssueType.PHONEME_FU.value
                        tip = TAXONOMY_EXPLANATIONS[JapaneseIssueType.PHONEME_FU]["practice_tip"]
                        mora_score = 70.0
                    # 3. Tsu sound
                    elif kana == "つ" and detected_kana in {"す", "ち", "と"}:
                        issue_type = JapaneseIssueType.PHONEME_TSU.value
                        tip = TAXONOMY_EXPLANATIONS[JapaneseIssueType.PHONEME_TSU]["practice_tip"]
                        mora_score = 60.0
                    # 4. Shi vs Chi
                    elif (kana == "し" and detected_kana == "ち") or (kana == "ち" and detected_kana == "し"):
                        issue_type = JapaneseIssueType.PHONEME_SHI_CHI.value
                        tip = "Phân biệt rõ âm 'shi' (vòm miệng mềm) và âm 'chi' (tắc xát đầu lưỡi)."
                        mora_score = 65.0
                    # 5. Voicing error (e.g. か vs が, た vs だ)
                    elif cls._is_voicing_pair(kana, detected_kana):
                        issue_type = JapaneseIssueType.VOICING_ERROR.value
                        tip = f"Âm「{kana}」và「{detected_kana}」chỉ khác nhau ở độ rung thanh quản (đục / trong)."
                        mora_score = 68.0
                    # 6. Yōon split
                    elif tm.special_type == "contracted":
                        issue_type = JapaneseIssueType.YOON.value
                        tip = TAXONOMY_EXPLANATIONS[JapaneseIssueType.YOON]["practice_tip"]
                        mora_score = 65.0
                    else:
                        mora_score = 75.0
                else:
                    # User omitted this mora completely (0% for omitted mora)
                    mora_score = 0.0
                    tip = f"Chưa phát âm mora「{kana}」."
            else:
                mora_score = 96.0

            total_mora_score += mora_score
            assessments.append(
                PhonemeAssessment(
                    mora_index=tm.mora_index,
                    kana=tm.kana,
                    target_phonemes=target_phonemes,
                    detected_sound_category=detected_kana,
                    score=mora_score,
                    confidence=0.9 if alignment_confidence == AnalysisConfidenceLevel.HIGH else 0.6,
                    issue_type=issue_type,
                    tip=tip,
                )
            )

        avg_score = round(total_mora_score / len(target_moras), 1)
        conf_val = 0.9 if alignment_confidence == AnalysisConfidenceLevel.HIGH else (0.65 if alignment_confidence == AnalysisConfidenceLevel.MEDIUM else 0.4)

        return (
            PronunciationScoreComponent(
                score=avg_score,
                confidence=conf_val,
                weight=0.25,
                available=True,
                interpretation=cls._interpret(avg_score),
            ),
            assessments,
        )

    @staticmethod
    def _is_voicing_pair(k1: str, k2: str) -> bool:
        pairs = {
            ("か", "が"), ("き", "ぎ"), ("く", "ぐ"), ("け", "げ"), ("こ", "ご"),
            ("さ", "ざ"), ("し", "じ"), ("す", "ず"), ("せ", "ぜ"), ("そ", "ぞ"),
            ("た", "だ"), ("ち", "ぢ"), ("つ", "づ"), ("て", "で"), ("と", "ど"),
            ("は", "ば"), ("ひ", "び"), ("ふ", "ぶ"), ("へ", "べ"), ("ほ", "ぼ"),
            ("は", "ぱ"), ("ひ", "ぴ"), ("ふ", "ぷ"), ("へ", "ぺ"), ("ほ", "ぽ"),
        }
        return (k1, k2) in pairs or (k2, k1) in pairs

    @staticmethod
    def _interpret(score: float) -> str:
        if score >= 90:
            return "Excellent"
        if score >= 80:
            return "Very Good"
        if score >= 70:
            return "Good"
        if score >= 60:
            return "Developing"
        return "Needs Attention"
