import re
from enum import Enum


class CoachIntent(str, Enum):
    SIMPLE_DATA = "simple_data"
    TREND = "trend"
    WEAKNESS = "weakness"
    RECOMMENDATION = "recommendation"
    DIAGNOSTIC = "diagnostic"
    WEEKLY_REVIEW = "weekly_review"
    GENERAL = "general"


class CoachIntentClassifier:
    """
    Fast, deterministic intent classifier for Personal AI Coach queries.
    Avoids expensive LLM calls for straightforward factual questions.
    """

    @staticmethod
    def classify(question: str) -> CoachIntent:
        q = question.lower().strip()

        # 1. Simple Data Questions
        if re.search(r"(bao nhiêu phút|bao nhiêu buổi|thời gian nói|streak|chuỗi|mấy ngày|how many minutes|how many sessions|current streak)", q):
            return CoachIntent.SIMPLE_DATA

        # 2. Weekly Review Questions
        if re.search(r"(tuần này|tổng kết tuần|tuần qua|this week|weekly review|weekly summary)", q):
            return CoachIntent.WEEKLY_REVIEW

        # 3. Weakness Questions
        if re.search(r"(yếu nhất|điểm yếu|yếu ở đâu|lỗi nào nhiều|biggest weakness|what is my weakness|weak points)", q):
            return CoachIntent.WEAKNESS

        # 4. Recommendation / What to practice
        if re.search(r"(nên luyện gì|hôm nay luyện gì|tập gì|bài tập nào|what should i practice|what to practice today|recommendation)", q):
            return CoachIntent.RECOMMENDATION

        # 5. Diagnostic / Why questions
        if re.search(r"(tại sao|sao lại|vì sao|không tự nhiên|sao nói chậm|grammar tốt mà|sao điểm|why is|why am i|why do)", q):
            return CoachIntent.DIAGNOSTIC

        # 6. Trend / Progress questions
        if re.search(r"(tiến bộ không|tiến bộ gì|có cải thiện không|cải thiện|am i improving|my progress|did i improve)", q):
            return CoachIntent.TREND

        return CoachIntent.GENERAL
