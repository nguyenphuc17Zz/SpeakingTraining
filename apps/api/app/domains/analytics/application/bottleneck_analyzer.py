from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.contracts import BottleneckAnalysis
from app.domains.analytics.domain.metric_definitions import ConfidenceLevel, MetricKey, MetricValue


class BottleneckAnalyzer:
    """
    Analyzes learning signals to identify the single most limiting bottleneck
    currently holding back the learner's Japanese conversational development.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def analyze_bottleneck(self, metrics: dict[str, MetricValue]) -> BottleneckAnalysis:
        """
        Deterministic decision tree evaluating observable performance signals.
        """
        grammar_val = metrics.get(MetricKey.GRAMMAR_ACCURACY.value)
        natural_val = metrics.get(MetricKey.NATURALNESS.value)
        speed_val = metrics.get(MetricKey.RESPONSE_SPEED.value)
        transfer_val = metrics.get(MetricKey.TRANSFER_RATE.value)
        mora_val = metrics.get(MetricKey.MORA_TIMING.value)
        exercise_succ = metrics.get(MetricKey.EXERCISE_SUCCESS_RATE.value)

        g_score = grammar_val.value if grammar_val else 75.0
        n_score = natural_val.value if natural_val else 70.0
        speed_ms = speed_val.value if speed_val else 1200.0
        transfer_pct = transfer_val.value if transfer_val else 60.0
        mora_score = mora_val.value if mora_val else 75.0
        drill_succ = exercise_succ.value if exercise_succ else 70.0

        evidence: list[str] = []

        # 1. Transfer Gap: Drills are mastered (>80%) but spontaneous production is low (<50%)
        if drill_succ >= 80.0 and transfer_pct < 55.0:
            evidence.append(f"Exercise success: {drill_succ}% vs Spontaneous transfer: {transfer_pct}%")
            return BottleneckAnalysis(
                candidate="Spontaneous Transfer Gap (自由発話への定着)",
                confidence=ConfidenceLevel.HIGH,
                description="Bạn nắm rất chắc cấu trúc trong bài tập và drill, nhưng chưa phản xạ tự nhiên trong hội thoại tự do. Kiến thức ngữ pháp không thiếu — cần chuyển trọng tâm sang roleplay thực chiến.",
                evidence_keys=evidence,
                suggested_focus="Spontaneous roleplay & free conversation",
            )

        # 2. Grammar Production Bottleneck
        if g_score < 65.0:
            evidence.append(f"Grammar accuracy: {g_score}%")
            return BottleneckAnalysis(
                candidate="Grammar Production (文法・助詞の運用力)",
                confidence=ConfidenceLevel.HIGH if (grammar_val and grammar_val.sample_size >= 4) else ConfidenceLevel.MEDIUM,
                description="Lỗi trợ từ và chia động từ còn xuất hiện thường xuyên, làm gián đoạn mạch diễn đạt. Hãy củng cố các mẫu ngữ pháp cơ bản trước khi tăng tốc độ hội thoại.",
                evidence_keys=evidence,
                suggested_focus="Targeted grammar & particle drills",
            )

        # 3. Response Latency / Hesitation Bottleneck (Grammar is okay, but speed is slow > 1800ms)
        if g_score >= 75.0 and speed_ms > 1800.0:
            evidence.append(f"Grammar: {g_score}%, Average response latency: {speed_ms}ms")
            return BottleneckAnalysis(
                candidate="Response Latency & Retrieval Speed (発話初動速度・瞬発力)",
                confidence=ConfidenceLevel.HIGH,
                description="Ngữ pháp của bạn khá chuẩn, nhưng thời gian suy nghĩ và tìm từ trước khi mở lời còn cao (>1.8s). Vấn đề là phản xạ truy xuất từ vựng dưới áp lực thời gian.",
                evidence_keys=evidence,
                suggested_focus="Timed response drills & speed sparring",
            )

        # 4. Naturalness & Nuance Bottleneck (Grammar is solid >80%, but Naturalness < 70%)
        if g_score >= 80.0 and n_score < 70.0:
            evidence.append(f"Grammar accuracy: {g_score}% vs Naturalness: {n_score}%")
            return BottleneckAnalysis(
                candidate="Naturalness & Pragmatic Nuance (表現の自然さ・敬語ニュアンス)",
                confidence=ConfidenceLevel.HIGH,
                description="Câu nói của bạn đúng ngữ pháp nhưng còn mang tính dịch từ (literal translation) hoặc thiếu đuôi câu tự nhiên (ね・よ) và chuyển đổi kính ngữ phù hợp ngữ cảnh.",
                evidence_keys=evidence,
                suggested_focus="Casual conversation & native phrase shadowing",
            )

        # 5. Mora & Rhythm Bottleneck (Mora timing < 65%)
        if mora_score < 65.0:
            evidence.append(f"Mora rhythm accuracy: {mora_score}%")
            return BottleneckAnalysis(
                candidate="Mora Timing & Rhythm (拍感覚・促音・長音)",
                confidence=ConfidenceLevel.MEDIUM,
                description="Khoảng cách trường âm và âm ngắt (sokuon) chưa chuẩn nhịp tiếng Nhật, khiến người nghe bản xứ cảm thấy ngắt quãng.",
                evidence_keys=evidence,
                suggested_focus="Mora timing & YouTube shadowing",
            )

        # Default: Balanced Progression
        return BottleneckAnalysis(
            candidate="Balanced Development (バランス良好)",
            confidence=ConfidenceLevel.HIGH,
            description="Các kỹ năng đang phát triển đồng đều. Hãy tiếp tục duy trì nhịp độ luyện tập đa dạng giữa hội thoại và shadowing.",
            evidence_keys=["All dimensions within normal progress thresholds"],
            suggested_focus="Maintain daily practice routine",
        )
