import json
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.contracts import AIUsage
from app.domains.ai.models import AIUsageRecord
from app.domains.ai.schemas import (
    AIRoutingPolicyRead,
    AIRoutingPolicyUpdate,
    AIUsageRecordRead,
    AIUsageSummaryRead,
)
from app.domains.settings.service import SettingsService
from app.domains.users.service import UserService
from app.shared.errors.exceptions import ValidationException


class AIUsageService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_service = UserService(session)

    async def record_usage(
        self,
        user_id: str,
        request_id: str,
        provider: str,
        model: str,
        task: str,
        latency_ms: int,
        usage: AIUsage | None = None,
        success: bool = True,
        error_type: str | None = None,
        fallback_occurred: bool = False,
        attempts_count: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> AIUsageRecord:
        input_tokens = usage.input_tokens if usage else None
        output_tokens = usage.output_tokens if usage else None
        total_tokens = usage.total_tokens if usage else (
            (input_tokens or 0) + (output_tokens or 0) if (input_tokens or output_tokens) else None
        )

        metadata_str = json.dumps(metadata) if metadata else None

        record = AIUsageRecord(
            user_id=user_id,
            request_id=request_id,
            provider=provider.lower().strip(),
            model=model,
            task=task.lower().strip(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            success=success,
            error_type=error_type,
            fallback_occurred=fallback_occurred,
            attempts_count=attempts_count,
            metadata_json=metadata_str,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def get_usage_summary(
        self,
        user_id: str | None = None,
        provider: str | None = None,
        task: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AIUsageSummaryRead:
        if not user_id:
            user = await self.user_service.get_or_create_default_user()
            user_id = user.id

        from sqlalchemy import case, func

        base_filter = [AIUsageRecord.user_id == user_id]
        if provider:
            base_filter.append(AIUsageRecord.provider == provider.lower().strip())
        if task:
            base_filter.append(AIUsageRecord.task == task.lower().strip())

        # 1. Single aggregate query directly in database
        agg_stmt = select(
            func.count(AIUsageRecord.id).label("total_requests"),
            func.sum(case((AIUsageRecord.success == True, 1), else_=0)).label("successful_requests"),
            func.coalesce(func.sum(AIUsageRecord.input_tokens), 0).label("total_input_tokens"),
            func.coalesce(func.sum(AIUsageRecord.output_tokens), 0).label("total_output_tokens"),
            func.coalesce(func.sum(AIUsageRecord.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.avg(AIUsageRecord.latency_ms), 0.0).label("avg_latency_ms"),
        ).where(*base_filter)

        agg_res = await self.session.execute(agg_stmt)
        agg_row = agg_res.one()

        total_requests = agg_row.total_requests or 0
        successful_requests = agg_row.successful_requests or 0
        failed_requests = total_requests - successful_requests
        total_input_tokens = int(agg_row.total_input_tokens or 0)
        total_output_tokens = int(agg_row.total_output_tokens or 0)
        total_tokens = int(agg_row.total_tokens or 0)
        avg_latency = float(agg_row.avg_latency_ms or 0.0)

        # 2. Fetch only paginated slice of records
        paged_stmt = (
            select(AIUsageRecord)
            .where(*base_filter)
            .order_by(desc(AIUsageRecord.created_at))
            .limit(limit)
            .offset(offset)
        )
        paged_res = await self.session.execute(paged_stmt)
        paged_records = paged_res.scalars().all()
        record_reads = [AIUsageRecordRead.model_validate(r) for r in paged_records]

        return AIUsageSummaryRead(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_tokens=total_tokens,
            avg_latency_ms=round(avg_latency, 2),
            recent_records=record_reads,
        )


class AIRoutingService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings_service = SettingsService(session)
        self.user_service = UserService(session)

    async def get_routing_policy(self, user_id: str | None = None) -> AIRoutingPolicyRead:
        if not user_id:
            user = await self.user_service.get_or_create_default_user()
            user_id = user.id

        settings = await self.settings_service.get_or_create_settings(user_id)
        priority_list = [p.strip() for p in settings.fallback_priority.split(",") if p.strip()]

        return AIRoutingPolicyRead(
            routing_mode=settings.routing_mode,
            preferred_provider=settings.default_ai_provider,
            default_model=settings.default_ai_model,
            fallback_enabled=settings.fallback_enabled,
            fallback_priority=priority_list,
        )

    async def update_routing_policy(
        self,
        payload: AIRoutingPolicyUpdate,
        user_id: str | None = None,
    ) -> AIRoutingPolicyRead:
        if not user_id:
            user = await self.user_service.get_or_create_default_user()
            user_id = user.id

        settings = await self.settings_service.get_or_create_settings(user_id)

        if payload.routing_mode is not None:
            mode = payload.routing_mode.lower().strip()
            if mode not in ("auto", "manual"):
                raise ValidationException("routing_mode must be 'auto' or 'manual'")
            settings.routing_mode = mode

        if payload.preferred_provider is not None:
            settings.default_ai_provider = payload.preferred_provider.lower().strip()

        if payload.default_model is not None:
            settings.default_ai_model = payload.default_model.strip()

        if payload.fallback_enabled is not None:
            settings.fallback_enabled = payload.fallback_enabled

        if payload.fallback_priority is not None:
            settings.fallback_priority = ",".join([p.lower().strip() for p in payload.fallback_priority if p.strip()])

        await self.session.commit()
        await self.session.refresh(settings)

        priority_list = [p.strip() for p in settings.fallback_priority.split(",") if p.strip()]
        return AIRoutingPolicyRead(
            routing_mode=settings.routing_mode,
            preferred_provider=settings.default_ai_provider,
            default_model=settings.default_ai_model,
            fallback_enabled=settings.fallback_enabled,
            fallback_priority=priority_list,
        )
