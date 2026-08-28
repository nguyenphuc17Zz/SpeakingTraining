import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.domain.insight_types import Insight, InsightLifecycle, InsightType
from app.domains.analytics.domain.metric_definitions import ConfidenceLevel, MetricKey, MetricValue, TrendLabel
from app.domains.analytics.models import InsightRecord


class InsightEngine:
    """
    Synthesizes actionable, diagnostic insights from learning metrics.
    Features cooldown deduplication, relevance ranking, and lifecycle tracking.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_insights(
        self, user_id: str, metrics: dict[str, MetricValue]
    ) -> list[Insight]:
        """
        Derives active insights and persists new ones with cooldown protection.
        """
        raw_insights: list[Insight] = []
        now = datetime.now(timezone.utc)

        # 1. Check Mora Timing / Pitch Accent Improvements or Plateaus
        mora = metrics.get(MetricKey.MORA_TIMING.value)
        if mora and mora.sample_size >= 4:
            if mora.trend in (TrendLabel.IMPROVING, TrendLabel.STRONGLY_IMPROVING):
                raw_insights.append(
                    Insight(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        insight_type=InsightType.IMPROVEMENT,
                        title="Tiến bộ vượt bậc về nhịp điệu Mora",
                        description=f"Độ chính xác về độ dài trường âm và ngắt âm đã tăng {mora.change:+0.1f}% trong {mora.sample_size} lần luyện tập gần nhất.",
                        confidence=mora.confidence,
                        metric_key=MetricKey.MORA_TIMING,
                        metric_value=mora.value,
                        action_hint="Thử thách với các video YouTube tốc độ 1.0x để duy trì cảm giác nhịp.",
                        action_target_type="shadowing",
                    )
                )
            elif mora.trend == TrendLabel.PLATEAU:
                raw_insights.append(
                    Insight(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        insight_type=InsightType.PLATEAU,
                        title="Điểm phát âm đang đi ngang",
                        description=f"Điểm mora timing duy trì quanh mức {mora.value:.0f}% qua nhiều lần phân tích. Thay vì lặp lại cùng một bài, hãy chuyển sang shadowing câu dài hơn.",
                        confidence=ConfidenceLevel.HIGH,
                        metric_key=MetricKey.MORA_TIMING,
                        metric_value=mora.value,
                        action_hint="Chuyển sang shadowing câu phức và hội thoại đời sống.",
                        action_target_type="shadowing",
                    )
                )

        # 2. Check Naturalness vs Grammar (Opportunity detection)
        grammar = metrics.get(MetricKey.GRAMMAR_ACCURACY.value)
        naturalness = metrics.get(MetricKey.NATURALNESS.value)
        if grammar and naturalness and grammar.sample_size >= 3:
            if grammar.value >= 80.0 and naturalness.value < 70.0:
                raw_insights.append(
                    Insight(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        insight_type=InsightType.OPPORTUNITY,
                        title="Cơ hội bứt phá: Từ 'đúng' sang 'tự nhiên'",
                        description=f"Ngữ pháp của bạn đã đạt {grammar.value:.0f}%, không còn là rào cản. Trọng tâm lúc này là chuyển dịch sang đuôi câu và kính ngữ tự nhiên.",
                        confidence=ConfidenceLevel.HIGH,
                        metric_key=MetricKey.NATURALNESS,
                        metric_value=naturalness.value,
                        action_hint="Tham gia 1 buổi roleplay 10 phút tập trung vào các đuôi câu ね / よ / かな.",
                        action_target_type="conversation",
                    )
                )

        # 3. Check Spontaneous Transfer Gap
        transfer = metrics.get(MetricKey.TRANSFER_RATE.value)
        drill_succ = metrics.get(MetricKey.EXERCISE_SUCCESS_RATE.value)
        if transfer and drill_succ and drill_succ.sample_size >= 4:
            if drill_succ.value >= 80.0 and transfer.value < 55.0:
                raw_insights.append(
                    Insight(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        insight_type=InsightType.TRANSFER_GAP,
                        title="Cần tăng cường vận dụng vào hội thoại tự do",
                        description=f"Bài tập đạt tỉ lệ đúng {drill_succ.value:.0f}%, nhưng tỉ lệ chuyển hoá sang phản xạ hội thoại mới đạt {transfer.value:.0f}%.",
                        confidence=ConfidenceLevel.HIGH,
                        metric_key=MetricKey.TRANSFER_RATE,
                        metric_value=transfer.value,
                        action_hint="Giảm bớt drill ngữ pháp đơn lẻ, chuyển sang hội thoại tình huống mở.",
                        action_target_type="conversation",
                    )
                )

        # 4. Consistency Insight
        const = metrics.get(MetricKey.LEARNING_CONSISTENCY.value)
        if const and const.sample_size >= 5:
            if const.value >= 70.0:
                raw_insights.append(
                    Insight(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        insight_type=InsightType.STRENGTH,
                        title="Duy trì nhịp độ học tập xuất sắc",
                        description=f"Bạn đã luyện tập đều đặn {const.value:.0f}% các ngày trong chu kỳ theo dõi. Thói quen hàng ngày là chìa khoá tạo phản xạ cơ miệng.",
                        confidence=ConfidenceLevel.HIGH,
                        metric_key=MetricKey.LEARNING_CONSISTENCY,
                        metric_value=const.value,
                        action_hint="Tiếp tục giữ vững chuỗi luyện tập hôm nay!",
                    )
                )

        # 5. Persist with 48h Cooldown Deduplication
        persisted: list[Insight] = []
        for ins in raw_insights:
            # Check recent insight with same type & metric
            cooldown_cutoff = now - timedelta(hours=48)
            existing_stmt = select(InsightRecord).where(
                InsightRecord.user_id == user_id,
                InsightRecord.insight_type == ins.insight_type.value,
                InsightRecord.metric_key == (ins.metric_key.value if ins.metric_key else None),
                InsightRecord.created_at >= cooldown_cutoff,
            )
            existing_res = await self.db.execute(existing_stmt)
            existing = existing_res.scalar_one_or_none()

            if not existing:
                record = InsightRecord(
                    id=ins.id,
                    user_id=user_id,
                    insight_type=ins.insight_type.value,
                    title=ins.title,
                    description=ins.description,
                    confidence=ins.confidence.value,
                    metric_key=ins.metric_key.value if ins.metric_key else None,
                    metric_value=ins.metric_value,
                    action_hint=ins.action_hint,
                    action_target_type=ins.action_target_type,
                    action_target_key=ins.action_target_key,
                    evidence_keys_json=ins.evidence_keys,
                    source_period=ins.source_period,
                    lifecycle="new",
                    expires_at=now + timedelta(days=7),
                )
                self.db.add(record)
                persisted.append(ins)
            else:
                # Reuse existing active insight
                persisted.append(
                    Insight(
                        id=existing.id,
                        user_id=existing.user_id,
                        insight_type=InsightType(existing.insight_type),
                        title=existing.title,
                        description=existing.description,
                        confidence=ConfidenceLevel(existing.confidence),
                        metric_key=MetricKey(existing.metric_key) if existing.metric_key else None,
                        metric_value=existing.metric_value,
                        action_hint=existing.action_hint,
                        action_target_type=existing.action_target_type,
                        action_target_key=existing.action_target_key,
                        lifecycle=InsightLifecycle(existing.lifecycle),
                        generated_at=existing.created_at,
                    )
                )

        await self.db.commit()
        return persisted
